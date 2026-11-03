# Heat Transfer Model for Anneraling in Bell-Type Furnaces

## Datos experimentales

Los datos utilizados de (Yang et al., 2025), fueron extraidos mediante IA, para tener, a grosso modo, datos experimentales con los cuales poder hacer una verificación del modelo implementado. 

### Posiciones de los termopares

La posición radial `r` se mide desde el eje vertical del horno. La posición vertical `z` se mide hacia arriba desde la base de la bobina correspondiente. Todas las distancias están expresadas en mm.

| Punto | Número de bobina | Ubicación | Posición radial, r (mm) | Posición vertical, z (mm) |
|---|---|---|---:|---:|
| 1 | — (encima de la bobina 4) | Hueco central, a la altura superior de la bobina 4 | Aproximadamente 0 | 1272 respecto a la base de la bobina 4 |
| 2 | 4 | Borde superior interior | Radio interior de la bobina 4 + 15 | 1272 |
| 3 | 4 | Borde superior exterior | 877.5 | 1272 |
| 4 | 4 | Interior de la bobina | 590.5 | 636 |
| 5 | 4 | Superficie exterior | 880.5 | 636 |
| 6 | 3 | Borde superior exterior | 914.0 | 1272 |
| 7 | 3 | Interior de la bobina | 608.5 | Aproximadamente 636 |
| 8 | 2 | Borde superior exterior | 929.0 | 1250 |
| 9 | 2 | Interior de la bobina | 620.5 | Aproximadamente 625 |
| 10 | 1 | Borde superior exterior | 927.0 | 1272 |
| 11 | 1 | Interior de la bobina | 615.5 | Aproximadamente 636 |
| 12 | — (debajo de la bobina 1) | Espacio central debajo de las bobinas | Aproximadamente 0 | −60 respecto a la cara superior de la placa de soporte |

Notas:
- Las bobinas están numeradas de abajo (1) hacia arriba (4).
- Las posiciones se interpretan de la Figura 8; los radios exteriores y las alturas se obtienen de la Tabla 3.
- Los puntos 7, 9 y 11 aparecen a media altura, pero sus posiciones verticales no están acotadas explícitamente.
- Los puntos 1 y 12 parecen estar sobre el eje vertical.
- Las coordenadas verticales utilizan referencias locales, no un origen único para todo el conjunto.

### Rollos

El ancho indicado en el artículo corresponde a la altura vertical de cada bobina en el conjunto apilado. El espesor corresponde a la lámina de acero.

| Número de bobina | Identificador | Tipo de acero | Diámetro exterior (mm) | Ancho (mm) | Espesor de la lámina (mm) | Longitud de la lámina (m) | Masa (kg) |
|---|---|---|---:|---:|---:|---:|---:|
| 1 | L179046800T | SPCC-PSR | 1869 | 1272 | 1.50 | 1634 | 24,490 |
| 2 | L179038800T | SPCC | 1867 | 1250 | 1.50 | 1629 | 23,993 |
| 3 | L179046600T | SPCC-PSR | 1837 | 1272 | 1.48 | 1593 | 23,557 |
| 4 | L179046700T | SPCC-PSR | 1761 | 1272 | 1.50 | 1428 | 21,417 |

Fuente: Figura 8 y Tabla 3 de [Yang et al. (2025)](https://doi.org/10.1038/s41598-025-97422-4).


## Citas

Yang, X.-j., Dai, F.-x., Bao, X.-j., Chen, G., Zhang, L., & Li, Y.-r. (2025). Study of heat transfer model and buried thermocouple test of bell-type annealing furnace based on thermal equilibrium. Scientific Reports, 15, Article 13362. https://doi.org/10.1038/s41598-025-97422-4