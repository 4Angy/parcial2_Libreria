# Spec Delta

## Purpose

Expone el estado del proceso y de su conexión con la base de datos, de modo que un operador o un orquestador puedan distinguir si la aplicación está viva de si además puede atender tráfico.

## ADDED Requirements

### Requirement: Sonda de vida

`GET /health/live` SHALL responder `200` con el cuerpo `{"estado": "vivo"}` sin consultar la base de datos.

#### Scenario: Proceso vivo con base caída

- **WHEN** se solicita `GET /health/live` mientras la base de datos no responde
- **THEN** la respuesta es `200`
- **AND** el cuerpo es `{"estado": "vivo"}`

#### Scenario: Proceso vivo con base disponible

- **WHEN** se solicita `GET /health/live` con la base disponible
- **THEN** la respuesta es `200`
- **AND** no se emite ninguna consulta a la base

### Requirement: Sonda de disponibilidad

`GET /health/ready` SHALL ejecutar `SELECT 1` contra la base y SHALL responder `200` con el estado de la conexión cuando la consulta funciona.

#### Scenario: Base disponible

- **WHEN** se solicita `GET /health/ready` y la base responde
- **THEN** la respuesta es `200`
- **AND** el cuerpo informa que la base está disponible

#### Scenario: Base no disponible

- **WHEN** se solicita `GET /health/ready` y la consulta a la base falla
- **THEN** la respuesta es `503`
- **AND** el cuerpo informa que la base no está disponible
- **AND** el cuerpo no incluye el texto interno del error de la base
