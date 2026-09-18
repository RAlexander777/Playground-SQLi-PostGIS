from sqlalchemy import Column, String, Numeric, Date, Integer, Text, Boolean
from geoalchemy2 import Geometry
from src.config.database import Base

class TgLote(Base):
    """
    Componente Gráfico y Alfanumérico del Lote Catastral (ISO 19152 - LA_SpatialUnit).
    SRID 32719 (WGS 84 / UTM Zona 19 Sur).
    """
    __tablename__ = 'tg_lote'

    id_lote = Column(String(14), primary_key=True, index=True)
    cod_sector = Column(String(4), index=True, nullable=False, default="0101")
    cod_mzn = Column(String(3), nullable=True)
    lote = Column(String(3), nullable=True)
    area_grafica = Column(Numeric(10, 2))
    peri_grafico = Column(Numeric(10, 2))
    tipo_suelo = Column(String(30), default="RESIDENCIAL_R3") # Datos de zonificación
    fech_actua = Column(Date)
    
    # Atributo geométrico principal
    objcad_lote_gemo = Column(
        Geometry(geometry_type='POLYGON', srid=32719, spatial_index=True), 
        nullable=True
    )

class UsuarioSistema(Base):
    """
    Tabla de credenciales administrativas y auditores catastrales.
    Objetivo para la exfiltración mediante Error-Based Spatial SQLi.
    """
    __tablename__ = 'catastro_usuarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(30), default="operador_catastral")
    email = Column(String(100))
    is_active = Column(Boolean, default=True)

class TitularPredio(Base):
    """
    Información patrimonial y tributaria del titular predial (ISO 19152 - LA_Party).
    """
    __tablename__ = 'catastro_titulares'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_lote = Column(String(14), index=True, nullable=False)
    dni_titular = Column(String(8), nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    autovaluo_soles = Column(Numeric(12, 2), nullable=False)
