# Manifiesto de corrida v2 — BORRADOR (pendiente del «sí» de lanzamiento de Alejandro)

_Preparado el 2026-10-21 tras el semáforo VERDE. No publicado todavía: publicar la imagen v2 y este manifiesto es acción externa que espera su sí al momento de lanzar (pre-registro §7.3)._

## Configuración declarada (ambos brazos)
- Revisor: `llm_reviewer_v2` (`RB_CONFIG_REVIEWER=v2`), una pasada por clase citando evidencia exacta + archivo head completo en contexto.
- Modelo: **gpt-5.6-sol**, effort **medium** (sin cambios respecto de v1).
- Única diferencia entre brazos: `governance` — base sin puerta; ALMA con puerta **alma-evidence-gate/1.3.0**, POLICY_SHA256 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`.
- Freno por PR: **US$6,50** (Adenda 4 al pre-registro v2, firmada por Alejandro el 21/10/2026). El valor en la bóveda del portal debe actualizarse a 6.50 antes de lanzar (acción de Alejandro) y este manifiesto lo declara.
- Tope duro de la práctica: **US$30** (congelado en §5; la regla de decisión del tope dio banda 1: proyección desde el semáforo ≈ US$8,6).

## Semáforo previo (2026-10-21)
- Batería sintética congelada de 8 códigos, hashes verificados 32/32 contra `MANIFIESTO-BATERIA.json`.
- base-v2: 16 hallazgos emitidos, 8/8 defectos plantados detectados. alma-v2: 6 emitidos, 6/8 detectados.
- Costo real total: **US$2,7457**. Veredicto: **VERDE** (criterio Adenda 3: ningún brazo en cero).
- Registro completo: `RESULTADO-SEMAFORO-20261021.md` (intentos 1 y 2 detenidos por credenciales, gasto US$0; intento 3 ejecutado, con incidente de infraestructura declarado y re-corrida solo de los casos cortados).
- Sin ajustes al sistema a partir del simulacro (regla del papel).

## Regla de avance (intacta, del pre-registro v2)
Se lanza la final solo si: F1_alma ≥ F1_base-v2 · precisión_alma ≥ precisión_base + 0,05 · caída de recall ≤ 0,03. Prueba de la linterna: el recall de base-v2 debe superar el 0,7% de la v1.
