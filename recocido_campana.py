"""
Calentamiento de un rollo de acero (cilindro hueco) en recocido en campana.
Comparación de dos aceros. Modelo 2D axisimétrico (r, z), volúmenes finitos, esquema explícito.

Ecuaciones tomadas del código previo, que a su vez se basa en:
  Yang et al., "Study of heat transfer model and buried thermocouple test of bell-type
  annealing furnace based on thermal equilibrium", Sci. Rep. 15:13362 (2025).
    - conductividad radial equivalente por red de resistencias (ecs. 9-17)
    - conductividad axial = k_acero * S/(S+b)
    - convección gas-rollo: Dittus-Boelter corregido (ecs. 7-8) y reparto de caudal (ecs. 5-6)

CAMBIOS RESPECTO AL CÓDIGO PREVIO
  * Un solo rollo (no una pila de 4).
  * El acero es un parámetro (clase Steel); se comparan dos.
  * Solo calentamiento: el gas sube con una rampa hasta T_obj y se mantiene ahí.
  * Salida: tiempo en que el punto más frío del rollo llega a T_obj - TOL.

Marcado con  # CALIBRAR  = dato que NO viene de una fuente citada: ajustar o justificar.
Unidades: SI (K, m, s, W, J/kg/K). Los perfiles de entrada/salida se manejan en °C.
"""
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt

SIGMA = 5.670374e-8  # Stefan-Boltzmann [W/m2K4]


# ----------------------------------------------------------------------------
# 1. PROPIEDADES DE LOS ACEROS (tablas en K; fuera de rango se mantiene el valor extremo)
# ----------------------------------------------------------------------------
@dataclass
class Steel:
    name: str
    T_k: np.ndarray    # [K]
    k: np.ndarray      # [W/mK]
    T_cp: np.ndarray   # [K]
    cp: np.ndarray     # [J/kgK]
    rho: float         # [kg/m3]

    def lam(self, T):
        return np.interp(T, self.T_k, self.k)

    def c(self, T):
        return np.interp(T, self.T_cp, self.cp)


C2K = 273.15

# AISI 1010 - Incropera et al. (6a ed., 2008), tabla A.1: 300, 400, 600, 800 y 1000 K.
# (se eliminó el punto de 1100 K del código previo: no pertenece a la tabla del 1010)
STEEL_1010 = Steel(
    name="AISI 1010 (Incropera)",
    T_k=np.array([300.0, 400.0, 600.0, 800.0, 1000.0]),
    k=np.array([63.9, 58.7, 48.8, 39.2, 31.3]),
    T_cp=np.array([300.0, 400.0, 600.0, 800.0, 1000.0]),
    cp=np.array([434.0, 487.0, 559.0, 685.0, 1168.0]),
    rho=7832.0,
)

# AISI 1008 - MatWeb, ficha MaterialData_6780.
# k(T) tabulada en °C. cp dado por rangos de temperatura: se usa el punto medio de cada rango.
# OJO: la ficha no da cp entre 750 y 850 °C (zona del pico de Curie); se interpola linealmente.
STEEL_1008 = Steel(
    name="AISI 1008 (MatWeb)",
    T_k=np.array([0, 100, 200, 400, 600, 800, 1000]) + C2K,
    k=np.array([65.2, 60.2, 54.7, 45.2, 36.3, 28.4, 27.3]),
    T_cp=np.array([100, 175, 225, 275, 375, 475, 575, 675, 725, 875]) + C2K,
    cp=1000.0 * np.array([0.481, 0.519, 0.536, 0.553, 0.595, 0.662, 0.754, 0.867, 1.105, 0.846]),
    rho=7872.0,
)


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
# 2. PARÁMETROS DE ENTRADA
# ----------------------------------------------------------------------------
@dataclass
class CoilSpec:
    ID: float = 0.508      # diámetro interior [m] = 20 in (dato del proyecto)
    OD: float = 1.869      # diámetro exterior [m]  PROVISIONAL: valor del artículo (Tabla 3), NO de Ternium
    W: float = 1.290       # ancho = altura axial [m]: máximo de la tabla Ternium de lámina en frío (756-1290 mm)
    S: float = 1.5e-3      # espesor de banda [m]: dentro del rango Ternium 0.26-3.40 mm   # CALIBRAR
    nr: int = 20           # celdas radiales
    nz: int = 24           # celdas axiales


@dataclass
class ContactParams:
    """Resistencia de contacto entre espiras (ecs. 9-17 del artículo)."""
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
    plate_gap: float = 0.015     # holgura de canal bajo/sobre plato convector [m] # CALIBRAR
    top_gap: float = 0.15        # holgura sobre el rollo [m]                      # CALIBRAR
    psi: float = 2.0             # realce por vórtices (ec. 7)                    # CALIBRAR
    xi: float = 1.0              # realce por radiación Tg>=800K (ec. 8)           # CALIBRAR
    bottom_adiabatic: bool = True  # rollo apoyado en la base (cara inferior adiabática)
    p_gas: float = 1.03e5        # presión absoluta del H2 [Pa]


@dataclass
class Programa:
    """Perfil del gas de protección (solo calentamiento)."""
    T0_C: float = 30.0           # temperatura inicial [°C]
    rampa_K_h: float = 50.0      # velocidad de calentamiento del gas [K/h]        # CALIBRAR
    TOL: float = 5.0             # el rollo "llegó" cuando T_fría >= T_obj - TOL [K]
    t_max_h: float = 200.0       # límite de tiempo de la simulación [h]
    dt_user: float = 30.0        # paso de tiempo máximo [s] (el de estabilidad puede ser menor)
    save_every_s: float = 300.0


def gas_temperature(t_s, T_obj_C, prog: Programa):
    """Tg [°C]: rampa lineal hasta T_obj y se mantiene."""
    return min(prog.T0_C + prog.rampa_K_h * t_s / 3600.0, T_obj_C)


# ----------------------------------------------------------------------------
# 3. REPARTO DE CAUDAL (ecs. 5 y 6) - para un solo rollo
# ----------------------------------------------------------------------------
def flow_distribution_single(Q):
    """Caudal por caras laterales (interior+exterior) y por el canal superior."""
    return Q, Q


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


def face_coefficients(Tg, coil: CoilSpec, fur: FurnaceSpec):
    """h en las 4 caras: (interior, exterior, superior, inferior)."""
    Q_side, Q_top = flow_distribution_single(fur.Q_total)
    A_in = np.pi / 4 * coil.ID ** 2
    A_out = np.pi / 4 * (fur.D_cover ** 2 - coil.OD ** 2)
    u_Q = Q_side / (A_in + A_out)                # misma velocidad en el hueco y en el anillo
    h_in = h_channel(Tg, u_Q * A_in, A_in, coil.ID, coil.W, fur)
    h_out = h_channel(Tg, u_Q * A_out, A_out, fur.D_cover - coil.OD, coil.W, fur)

    r_circ = np.pi * (coil.ID + coil.OD) / 2.0
    L_pl = (coil.OD - coil.ID) / 2.0
    h_top = h_channel(Tg, Q_top, r_circ * fur.top_gap, 2 * fur.top_gap, L_pl, fur)
    h_bot = 0.0 if fur.bottom_adiabatic else h_channel(
        Tg, 0.1 * Q_side, r_circ * fur.plate_gap, 2 * fur.plate_gap, L_pl, fur)
    return h_in, h_out, h_top, h_bot


# ----------------------------------------------------------------------------
# 5. CONDUCTIVIDAD RADIAL EQUIVALENTE (ecs. 9-17)
# ----------------------------------------------------------------------------
def lambda_radial(Tm, S, cp_: ContactParams, lam_g, emulsion_active, steel: Steel):
    """
    Resistencia total en serie: R_acero + R_óxido (o emulsión) + (R_rad || R_gas || R_contacto).
    """
    P, H = cp_.P, cp_.H
    phi = P / (H + P)                              # ec. 14
    b = 42.7e-6 * np.exp(-0.05 * P)                # ec. 15  [m]
    lam_S = steel.lam(Tm)
    g_rad = 4 * (1 - phi) * cp_.eps * SIGMA * Tm ** 3 / (2 - cp_.eps)      # ec. 11
    g_gas = (1 - phi) * lam_g / b                                           # ec. 12
    g_con = 1.13 * lam_S * cp_.tan_theta * phi ** 0.94 / cp_.sigma_p        # ec. 13
    R_par = 1.0 / (g_rad + g_gas + g_con)
    R_S = S / lam_S
    if emulsion_active:   # Tg < 800 K en calentamiento: ec. 17, rama inferior
        return cp_.eta * (S + b) / (R_S + R_par)
    R_O = cp_.b_O / cp_.lam_O
    return (S + b + cp_.b_O) / (R_S + R_O + R_par)


# ----------------------------------------------------------------------------
# 6. SOLVER DEL ROLLO (equilibrio térmico en volúmenes de control)
# ----------------------------------------------------------------------------
class CoilModel:
    def __init__(self, spec: CoilSpec, steel: Steel, T0_K, contact: ContactParams):
        self.s, self.steel, self.cp_ = spec, steel, contact
        s = spec
        self.dr = (s.OD - s.ID) / 2.0 / s.nr
        self.dz = s.W / s.nz
        self.r_c = s.ID / 2.0 + (np.arange(s.nr) + 0.5) * self.dr
        self.r_w = self.r_c - self.dr / 2
        self.r_e = self.r_c + self.dr / 2
        self.V = (self.r_c * self.dr * self.dz)[:, None]          # (nr,1) por radián
        self.T = np.full((s.nr, s.nz), float(T0_K))
        self.b = 42.7e-6 * np.exp(-0.05 * contact.P)
        self.emulsion_burned = False

    def derivative(self, Tg, h4):
        """dT/dt y dt máximo estable (criterio ec. 4 generalizado)."""
        s, T, st = self.s, self.T, self.steel
        h_in, h_out, h_top, h_bot = h4
        rho_eff = st.rho * s.S / (s.S + self.b)      # densidad aparente del rollo
        c = st.c(T)
        _, _, lam_g, _ = gas_props(T)
        emulsion = (Tg < self.cp_.T_switch) and not self.emulsion_burned
        lam_r = lambda_radial(T, s.S, self.cp_, lam_g, emulsion, st)
        lam_z = st.lam(T) * s.S / (s.S + self.b)

        def harm(a, b_):
            return 2 * a * b_ / (a + b_)

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
# 7. SIMULACIÓN DE UN CALENTAMIENTO
# ----------------------------------------------------------------------------
def calentar(steel, T_obj_C, coil=None, fur=None, contact=None, prog=None):
    """Calienta hasta que T_fría >= T_obj - TOL. Devuelve (modelo, historia, t_llegada_h)."""
    coil, fur = coil or CoilSpec(), fur or FurnaceSpec()
    contact, prog = contact or ContactParams(), prog or Programa()
    m = CoilModel(coil, steel, prog.T0_C + C2K, contact)

    t, t_end = 0.0, prog.t_max_h * 3600.0
    hist = {"t": [], "Tg": [], "cold": [], "hot": []}
    next_save, t_reach = 0.0, np.nan
    while t < t_end:
        Tg_C = gas_temperature(t, T_obj_C, prog)
        Tg = Tg_C + C2K
        if Tg >= contact.T_switch:
            m.emulsion_burned = True
        d, dt_stab = m.derivative(Tg, face_coefficients(Tg, coil, fur))
        dt = min(prog.dt_user, 0.9 * dt_stab)
        m.T += dt * d
        t += dt
        if t >= next_save:
            hist["t"].append(t / 3600.0); hist["Tg"].append(Tg_C)
            hist["cold"].append(m.T.min() - C2K); hist["hot"].append(m.T.max() - C2K)
            next_save += prog.save_every_s
        if m.T.min() - C2K >= T_obj_C - prog.TOL:
            t_reach = t / 3600.0
            break
    return m, {k: np.array(v) for k, v in hist.items()}, t_reach


# ----------------------------------------------------------------------------
# 8. COMPARACIÓN
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    ACEROS = [STEEL_1010, STEEL_1008]
    T_OBJ = [580, 680, 780]          # °C

    coil, prog = CoilSpec(), Programa()
    print(f"ID = {coil.ID*1000:.0f} mm, OD = {coil.OD*1000:.0f} mm (provisional), "
          f"ancho = {coil.W*1000:.0f} mm, espesor banda = {coil.S*1000:.2f} mm")
    print(f"rampa del gas = {prog.rampa_K_h:g} K/h, tolerancia = {prog.TOL:g} K\n")

    res, hist780, mods780 = {}, {}, {}
    for T_obj in T_OBJ:
        fila = []
        for st in ACEROS:
            m, h, t_reach = calentar(st, T_obj, coil=coil, prog=prog)
            res[(T_obj, st.name)] = t_reach
            if T_obj == 780:
                hist780[st.name], mods780[st.name] = h, m
            fila.append(f"{st.name}: {t_reach:6.2f} h")
        print(f"T_obj = {T_obj} °C | " + " | ".join(fila))

    # Gráficas
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for st in ACEROS:
        h = hist780[st.name]
        ax[0].plot(h["t"], h["cold"], label=f"{st.name} - punto frío")
        ax[0].plot(h["t"], h["hot"], "--", label=f"{st.name} - punto caliente")
    ax[0].plot(h["t"], h["Tg"], "r", lw=1.5, label="Gas (dato)")
    ax[0].set_xlabel("t [h]"); ax[0].set_ylabel("T [°C]"); ax[0].legend(fontsize=7)
    ax[0].set_title("Calentamiento hasta 780 °C")

    st = ACEROS[0]; m = mods780[st.name]
    r = m.r_c; z = (np.arange(m.s.nz) + 0.5) * m.dz
    im = ax[1].pcolormesh(r, z, (m.T - C2K).T, shading="auto", cmap="jet")
    plt.colorbar(im, ax=ax[1], label="°C")
    ax[1].set_xlabel("r [m]"); ax[1].set_ylabel("z [m]")
    ax[1].set_title(f"Campo de T al llegar a 780 °C - {st.name}")
    plt.tight_layout()
    plt.savefig("resultado_recocido.png", dpi=130)
    plt.show()
