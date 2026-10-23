"""
Simulación 2D axisimétrica del recocido en campana (hidrógeno) de una pila de bobinas.

Basado en: Yang et al., "Study of heat transfer model and buried thermocouple test of
bell-type annealing furnace based on thermal equilibrium", Sci. Rep. 15:13362 (2025).

Qué hace:
  * Cada bobina se discretiza en celdas (r, z). Cada celda es un volumen de control
    (método de equilibrio térmico / volúmenes finitos, esquema explícito).
  * La temperatura del gas de protección Tg(t) es DATO (termopar de control).
  * Conducción radial con conductividad equivalente lambda_r (red de resistencias,
    ecs. 9-17 del artículo) y axial con lambda_z.
  * Convección gas-bobina en las 4 caras (interior, exterior, superior, inferior) con
    Dittus-Boelter corregido (ec. 7) y reparto de caudal entre canales (ecs. 5-6).

TODO lo marcado con  # CALIBRAR  son parámetros que el artículo no publica o que
dependen de tu horno: ajústalos con termopares enterrados / datos de planta.

Unidades: SI (K, m, s, W, J/kg/K). Las temperaturas de entrada/salida de los perfiles
se manejan en °C por comodidad y se convierten internamente a K.
"""
from dataclasses import dataclass, field
import numpy as np

SIGMA = 5.670374e-8  # Stefan-Boltzmann [W/m2K4]


# ----------------------------------------------------------------------------
# 1. PROPIEDADES DE MATERIALES
# ----------------------------------------------------------------------------
# Acero bajo carbono (valores aprox. tipo AISI 1010). Sustituye por los de tu acero.
_T_TAB = np.array([300.0, 400.0, 600.0, 800.0, 1000.0, 1100.0])
_LAM_TAB = np.array([63.9, 58.7, 48.8, 39.2, 31.3, 28.0])        # W/mK
_CP_TAB = np.array([434.0, 487.0, 559.0, 685.0, 1169.0, 700.0])  # J/kgK (pico ~Curie/A1)


def lam_steel(T):
    return np.interp(T, _T_TAB, _LAM_TAB)


def cp_steel(T):
    return np.interp(T, _T_TAB, _CP_TAB)


def gas_props(T, p=1.03e5):
    """Hidrógeno: densidad (gas ideal), viscosidad (Sutherland), conductividad, Pr."""
    T = np.asarray(T, dtype=float)
    M, R = 2.016e-3, 8.314
    rho = p * M / (R * T)
    mu = 8.411e-6 * (T / 273.0) ** 1.5 * (273.0 + 97.0) / (T + 97.0)
    lam = 0.1805 * (T / 300.0) ** 0.8
    cp = 14300.0
    Pr = mu * cp / lam
    return rho, mu, lam, Pr


# ----------------------------------------------------------------------------
# 2. PARÁMETROS
# ----------------------------------------------------------------------------
@dataclass
class CoilSpec:
    ID: float = 0.61       # diámetro interior [m]  (no viene en el artículo)  # CALIBRAR
    OD: float = 1.869      # diámetro exterior [m]  (Tabla 3, coil 1#)
    W: float = 1.272       # ancho de la bobina = altura axial [m]
    S: float = 1.5e-3      # espesor de banda [m]
    nr: int = 20           # celdas radiales
    nz: int = 24           # celdas axiales
    rho: float = 7850.0    # densidad del acero [kg/m3]


@dataclass
class ContactParams:
    """Parámetros de la resistencia de contacto entre espiras (ecs. 9-17)."""
    P: float = 8.0               # presión de contacto [MPa]         (artículo)
    H: float = 1133.86           # dureza [MPa]                      (artículo)
    eps: float = 0.08554         # emisividad                        (artículo)
    sigma_p: float = 3.2215e-6   # rugosidad [m]                     (artículo)
    tan_theta: float = 0.20      # pendiente media de rugosidad      # CALIBRAR
    b_O: float = 10e-6           # espesor capa de óxido [m]         (artículo)
    lam_O: float = 3.0           # conductividad del óxido [W/mK]    # CALIBRAR
    eta: float = 1.0             # corrección por emulsión (<800 K)  # CALIBRAR
    T_switch: float = 800.0      # K, cambio emulsión -> óxido


@dataclass
class FurnaceSpec:
    D_cover: float = 2.15        # diámetro interior de la campana interior [m]   # CALIBRAR
    Q_total: float = 30.0        # caudal volumétrico del ventilador [m3/s]       # CALIBRAR
    zeta_inv: float = 0.909      # 1/zeta: atenuación del caudal (artículo)
    plate_gap: float = 0.015     # holgura de canal bajo/sobre plato convector [m] # CALIBRAR
    top_gap: float = 0.15        # holgura sobre la última bobina [m]              # CALIBRAR
    psi: float = 2.0             # realce por vórtices (ec. 7)                    # CALIBRAR
    xi: float = 1.0              # realce por radiación Tg>=800K (ec. 8)           # CALIBRAR
    bottom_adiabatic: bool = True  # bobina 1 apoyada en la base (artículo: 3 caras)
    p_gas: float = 1.03e5        # presión absoluta del H2 [Pa]


# ----------------------------------------------------------------------------
# 3. REPARTO DE CAUDAL (ecs. 5 y 6)
# ----------------------------------------------------------------------------
def flow_distribution(n_coils, Q, zeta_inv=0.909):
    """
    Devuelve:
      Q_plate[k] : caudal por el plato convector k (entre bobina k y k+1), k=0..n-2
      Q_side[k]  : caudal por las caras interior+exterior de la bobina k
      Q_top      : caudal por el canal superior
    Extrapolación a n_coils != 4 (el artículo solo da el caso de 4):
      fd_{n-1} = 1/(2+n),  fd_{k} = zeta * fd_{k+1}   (zeta = 1/0.909)
    """
    zeta = 1.0 / zeta_inv
    n_pl = n_coils - 1
    fd = np.zeros(n_pl)
    if n_pl > 0:
        fd[-1] = 1.0 / (2 + n_coils)
        for k in range(n_pl - 2, -1, -1):
            fd[k] = zeta * fd[k + 1]
    Q_plate = np.zeros(n_pl)
    remaining = Q
    Q_side = np.zeros(n_coils)
    for k in range(n_coils):
        Q_side[k] = remaining               # lo que sigue pasando por la bobina k
        if k < n_pl:
            Q_plate[k] = remaining * fd[k]
            remaining = remaining * (1.0 - fd[k])
    Q_top = remaining
    return Q_plate, Q_side, Q_top


# ----------------------------------------------------------------------------
# 4. COEFICIENTE DE CONVECCIÓN (ecs. 7 y 8)
# ----------------------------------------------------------------------------
def h_channel(Tg, Q, A, D, L, fur: FurnaceSpec):
    rho, mu, lam, Pr = gas_props(Tg, fur.p_gas)
    u = Q / A
    Re = rho * u * D / mu
    # Dittus-Boelter (calentamiento, n=0.4) + corrección de entrada (1+(D/L)^0.7)
    Nu = 0.023 * fur.psi * Re ** 0.8 * Pr ** 0.4 * (1.0 + (D / L) ** 0.7)
    h = Nu * lam / D
    return fur.xi * h if Tg >= 800.0 else h


def face_coefficients(Tg, k, n_coils, coil: CoilSpec, fur: FurnaceSpec, flows):
    """h en las 4 caras de la bobina k: (interior, exterior, superior, inferior)."""
    Q_plate, Q_side, Q_top = flows
    A_in = np.pi / 4 * coil.ID ** 2
    A_out = np.pi / 4 * (fur.D_cover ** 2 - coil.OD ** 2)
    u_eq_Q = Q_side[k] / (A_in + A_out)       # misma velocidad en bore y anillo
    h_in = h_channel(Tg, u_eq_Q * A_in, A_in, coil.ID, coil.W, fur)
    h_out = h_channel(Tg, u_eq_Q * A_out, A_out, fur.D_cover - coil.OD, coil.W, fur)

    r_circ = np.pi * (coil.ID + coil.OD) / 2.0
    L_pl = (coil.OD - coil.ID) / 2.0

    def h_gap(Qg, gap):
        return h_channel(Tg, Qg, r_circ * gap, 2 * gap, L_pl, fur)

    # cara superior
    if k < n_coils - 1:
        h_top = h_gap(Q_plate[k] / 2.0, fur.plate_gap)      # el plato reparte mitad/mitad
    else:
        h_top = h_gap(Q_top, fur.top_gap)
    # cara inferior
    if k == 0:
        h_bot = 0.0 if fur.bottom_adiabatic else h_gap(Q_side[0] * 0.1, fur.plate_gap)
    else:
        h_bot = h_gap(Q_plate[k - 1] / 2.0, fur.plate_gap)
    return h_in, h_out, h_top, h_bot


# ----------------------------------------------------------------------------
# 5. CONDUCTIVIDAD RADIAL EQUIVALENTE (ecs. 9-17)
# ----------------------------------------------------------------------------
def lambda_radial(Tm, S, cp_: ContactParams, lam_g, emulsion_active):
    """
    Tm: temperatura de cada celda [K] (array). lam_g: conductividad del gas a Tm.
    Resistencia total en serie:  R = S/lamS (=2*R_S/2) + R_O(o R_E) + 1/(1/R_R+1/R_G+1/R_D)
    """
    P, H = cp_.P, cp_.H
    phi = P / (H + P)                              # ec. 14
    b = 42.7e-6 * np.exp(-0.05 * P)                # ec. 15  [m]
    lam_S = lam_steel(Tm)
    # conductancias en paralelo (inversas de R_R, R_G, R_D)
    g_rad = 4 * (1 - phi) * cp_.eps * SIGMA * Tm ** 3 / (2 - cp_.eps)    # ec. 11
    g_gas = (1 - phi) * lam_g / b                                         # ec. 12
    g_con = 1.13 * lam_S * cp_.tan_theta * phi ** 0.94 / cp_.sigma_p      # ec. 13
    R_par = 1.0 / (g_rad + g_gas + g_con)
    R_S = S / lam_S
    if emulsion_active:   # Tg < 800 K en calentamiento: ec. 17 rama inferior
        return cp_.eta * (S + b) / (R_S + R_par)
    R_O = cp_.b_O / cp_.lam_O
    return (S + b + cp_.b_O) / (R_S + R_O + R_par)


# ----------------------------------------------------------------------------
# 6. SOLVER POR BOBINA (equilibrio térmico en volúmenes de control)
# ----------------------------------------------------------------------------
class CoilModel:
    def __init__(self, spec: CoilSpec, T0, contact: ContactParams, cylindrical=True):
        self.s, self.cp_ = spec, contact
        s = spec
        self.dr = (s.OD - s.ID) / 2.0 / s.nr
        self.dz = s.W / s.nz
        rc = s.ID / 2.0 + (np.arange(s.nr) + 0.5) * self.dr
        if cylindrical:
            self.r_c = rc
            self.r_w = rc - self.dr / 2
            self.r_e = rc + self.dr / 2
        else:                       # versión "plana" del artículo
            self.r_c = self.r_w = self.r_e = np.ones(s.nr)
        self.V = (self.r_c * self.dr * self.dz)[:, None]          # (nr,1) por radián
        self.T = np.full((s.nr, s.nz), float(T0))
        self.b = 42.7e-6 * np.exp(-0.05 * contact.P)
        self.emulsion_burned = False

    def derivative(self, Tg, h4):
        """dT/dt y dt máximo estable (criterio ec. 4 generalizado)."""
        s, T = self.s, self.T
        h_in, h_out, h_top, h_bot = h4
        rho_eff = s.rho * s.S / (s.S + self.b)      # densidad aparente de la bobina
        c = cp_steel(T)
        rho_g, mu_g, lam_g, Pr = gas_props(T)
        emulsion = (Tg < self.cp_.T_switch) and not self.emulsion_burned
        lam_r = lambda_radial(T, s.S, self.cp_, lam_g, emulsion)
        lam_z = lam_steel(T) * s.S / (s.S + self.b)

        def harm(a, b_):  # media armónica en la cara
            return 2 * a * b_ / (a + b_)

        # conductancias entre celdas vecinas [W/K]
        G_r = harm(lam_r[:-1, :], lam_r[1:, :]) * (self.r_e[:-1, None] * self.dz / self.dr)
        G_z = harm(lam_z[:, :-1], lam_z[:, 1:]) * (self.r_c[:, None] * self.dr / self.dz)

        Q = np.zeros_like(T)
        Gs = np.zeros_like(T)
        dTr = T[1:, :] - T[:-1, :]
        Q[:-1, :] += G_r * dTr;  Q[1:, :] -= G_r * dTr
        Gs[:-1, :] += G_r;       Gs[1:, :] += G_r
        dTz = T[:, 1:] - T[:, :-1]
        Q[:, :-1] += G_z * dTz;  Q[:, 1:] -= G_z * dTz
        Gs[:, :-1] += G_z;       Gs[:, 1:] += G_z

        # fronteras convectivas con el gas
        Gb = h_in * self.r_w[0] * self.dz
        Q[0, :] += Gb * (Tg - T[0, :]);   Gs[0, :] += Gb
        Gb = h_out * self.r_e[-1] * self.dz
        Q[-1, :] += Gb * (Tg - T[-1, :]); Gs[-1, :] += Gb
        Gb = h_top * self.r_c * self.dr
        Q[:, -1] += Gb * (Tg - T[:, -1]); Gs[:, -1] += Gb
        Gb = h_bot * self.r_c * self.dr
        Q[:, 0] += Gb * (Tg - T[:, 0]);   Gs[:, 0] += Gb

        C = rho_eff * c * self.V                    # capacidad térmica [J/K]
        return Q / C, float(np.min(C / np.maximum(Gs, 1e-12)))


# ----------------------------------------------------------------------------
# 7. SIMULACIÓN COMPLETA
# ----------------------------------------------------------------------------
def gas_profile_example(t_s):
    """Perfil de Tg [°C] -> aprox. de la Fig. 10 (sin la falla de combustión). EDÍTALO."""
    pts_h = np.array([0, 1, 3, 12, 17.5, 18, 24, 35.0])
    pts_C = np.array([30, 280, 380, 705, 705, 560, 400, 150.0])
    return np.interp(t_s / 3600.0, pts_h, pts_C)


def simulate(coils, fur=None, contact=None, Tg_fun=gas_profile_example, t_end_h=35.0,
             dt_user=30.0, T0_C=30.0, save_every_s=300.0, cylindrical=True, verbose=True):
    fur = fur or FurnaceSpec()
    contact = contact or ContactParams()
    n = len(coils)
    models = [CoilModel(c, T0_C + 273.15, contact, cylindrical) for c in coils]
    flows = flow_distribution(n, fur.Q_total, fur.zeta_inv)

    t, t_end = 0.0, t_end_h * 3600.0
    hist = {"t": [], "Tg": [], "cold": [[] for _ in range(n)], "hot": [[] for _ in range(n)],
            "center": [[] for _ in range(n)]}
    next_save = 0.0
    n_steps = 0
    while t < t_end:
        Tg = Tg_fun(t) + 273.15
        if Tg >= contact.T_switch:
            for m in models:
                m.emulsion_burned = True
        derivs, dts = [], []
        for k, m in enumerate(models):
            h4 = face_coefficients(Tg, k, n, coils[k], fur, flows)
            d, dtm = m.derivative(Tg, h4)
            derivs.append(d); dts.append(dtm)
        dt = min(dt_user, 0.9 * min(dts), t_end - t)     # estabilidad explícita
        for m, d in zip(models, derivs):
            m.T += dt * d
        t += dt
        n_steps += 1
        if t >= next_save:
            hist["t"].append(t / 3600.0); hist["Tg"].append(Tg - 273.15)
            for k, m in enumerate(models):
                hist["cold"][k].append(m.T.min() - 273.15)
                hist["hot"][k].append(m.T.max() - 273.15)
                hist["center"][k].append(m.T[m.s.nr // 2, m.s.nz // 2] - 273.15)
            next_save += save_every_s
    if verbose:
        print(f"pasos: {n_steps}, dt mínimo estable ~ {min(dts):.1f} s")
    return models, {k: (np.array(v) if not isinstance(v, list) or not v or not isinstance(v[0], list)
                        else [np.array(x) for x in v]) for k, v in hist.items()}


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 4 bobinas apiladas (diámetros exteriores de la Tabla 3 del artículo)
    coils = [CoilSpec(OD=1.869), CoilSpec(OD=1.867), CoilSpec(OD=1.837), CoilSpec(OD=1.761)]
    models, h = simulate(coils)

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    ax[0].plot(h["t"], h["Tg"], "r", lw=2, label="Gas (dato)")
    for k in range(4):
        ax[0].plot(h["t"], h["hot"][k], "--", label=f"{k+1}# punto caliente")
        ax[0].plot(h["t"], h["cold"][k], label=f"{k+1}# punto frío")
    ax[0].set_xlabel("t [h]"); ax[0].set_ylabel("T [°C]"); ax[0].legend(fontsize=7, ncol=2)
    ax[0].set_title("Evolución de temperaturas")

    m = models[1]
    r = m.s.ID / 2 + (np.arange(m.s.nr) + 0.5) * m.dr
    z = (np.arange(m.s.nz) + 0.5) * m.dz
    im = ax[1].pcolormesh(r, z, (m.T - 273.15).T, shading="auto", cmap="jet")
    plt.colorbar(im, ax=ax[1], label="°C")
    ax[1].set_xlabel("r [m]"); ax[1].set_ylabel("z [m]")
    ax[1].set_title("Campo de T final, bobina 2#")
    plt.tight_layout(); plt.savefig("resultado_recocido.png", dpi=130)

    for k in range(4):
        i = int(np.argmax(h["cold"][k]))
        print(f"Bobina {k+1}: T_fría máx = {h['cold'][k][i]:.1f} °C a las {h['t'][i]:.1f} h; "
              f"T_caliente máx = {max(h['hot'][k]):.1f} °C")
