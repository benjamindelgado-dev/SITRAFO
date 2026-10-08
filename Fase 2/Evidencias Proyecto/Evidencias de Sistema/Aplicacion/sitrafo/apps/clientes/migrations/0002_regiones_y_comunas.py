"""
Carga las 16 regiones y las 346 comunas de Chile (RF-CLI-04).

Hasta ahora solo existia la comuna que crea cargar_demo (Puente Alto), por lo
que el cliente no podia registrar direcciones en otras comunas. Es una
migracion de datos para que cada despliegue (Render ejecuta migrate) quede
con el catalogo completo sin comandos manuales.

Es idempotente: usa get_or_create por nombre, de modo que respeta la region
y la comuna que ya hubiera creado cargar_demo. No tiene reversa destructiva,
porque las direcciones registradas referencian estas comunas.
"""
from django.db import migrations

REGIONES = [
    ("XV", "Arica y Parinacota", [
        "Arica", "Camarones", "Putre", "General Lagos"]),
    ("I", "Tarapacá", [
        "Iquique", "Alto Hospicio", "Pozo Almonte", "Camiña", "Colchane", "Huara", "Pica"]),
    ("II", "Antofagasta", [
        "Antofagasta", "Mejillones", "Sierra Gorda", "Taltal", "Calama", "Ollagüe",
        "San Pedro de Atacama", "Tocopilla", "María Elena"]),
    ("III", "Atacama", [
        "Copiapó", "Caldera", "Tierra Amarilla", "Chañaral", "Diego de Almagro",
        "Vallenar", "Alto del Carmen", "Freirina", "Huasco"]),
    ("IV", "Coquimbo", [
        "La Serena", "Coquimbo", "Andacollo", "La Higuera", "Paiguano", "Vicuña",
        "Illapel", "Canela", "Los Vilos", "Salamanca", "Ovalle", "Combarbalá",
        "Monte Patria", "Punitaqui", "Río Hurtado"]),
    ("V", "Valparaíso", [
        "Valparaíso", "Casablanca", "Concón", "Juan Fernández", "Puchuncaví", "Quintero",
        "Viña del Mar", "Isla de Pascua", "Los Andes", "Calle Larga", "Rinconada",
        "San Esteban", "La Ligua", "Cabildo", "Papudo", "Petorca", "Zapallar", "Quillota",
        "La Calera", "Hijuelas", "La Cruz", "Nogales", "San Antonio", "Algarrobo",
        "Cartagena", "El Quisco", "El Tabo", "Santo Domingo", "San Felipe", "Catemu",
        "Llaillay", "Panquehue", "Putaendo", "Santa María", "Quilpué", "Limache", "Olmué",
        "Villa Alemana"]),
    ("RM", "Metropolitana de Santiago", [
        "Santiago", "Cerrillos", "Cerro Navia", "Conchalí", "El Bosque", "Estación Central",
        "Huechuraba", "Independencia", "La Cisterna", "La Florida", "La Granja",
        "La Pintana", "La Reina", "Las Condes", "Lo Barnechea", "Lo Espejo", "Lo Prado",
        "Macul", "Maipú", "Ñuñoa", "Pedro Aguirre Cerda", "Peñalolén", "Providencia",
        "Pudahuel", "Quilicura", "Quinta Normal", "Recoleta", "Renca", "San Joaquín",
        "San Miguel", "San Ramón", "Vitacura", "Puente Alto", "Pirque", "San José de Maipo",
        "Colina", "Lampa", "Tiltil", "San Bernardo", "Buin", "Calera de Tango", "Paine",
        "Melipilla", "Alhué", "Curacaví", "María Pinto", "San Pedro", "Talagante",
        "El Monte", "Isla de Maipo", "Padre Hurtado", "Peñaflor"]),
    ("VI", "Libertador General Bernardo O'Higgins", [
        "Rancagua", "Codegua", "Coinco", "Coltauco", "Doñihue", "Graneros", "Las Cabras",
        "Machalí", "Malloa", "Mostazal", "Olivar", "Peumo", "Pichidegua",
        "Quinta de Tilcoco", "Rengo", "Requínoa", "San Vicente", "Pichilemu", "La Estrella",
        "Litueche", "Marchigüe", "Navidad", "Paredones", "San Fernando", "Chépica",
        "Chimbarongo", "Lolol", "Nancagua", "Palmilla", "Peralillo", "Placilla", "Pumanque",
        "Santa Cruz"]),
    ("VII", "Maule", [
        "Talca", "Constitución", "Curepto", "Empedrado", "Maule", "Pelarco", "Pencahue",
        "Río Claro", "San Clemente", "San Rafael", "Cauquenes", "Chanco", "Pelluhue",
        "Curicó", "Hualañé", "Licantén", "Molina", "Rauco", "Romeral", "Sagrada Familia",
        "Teno", "Vichuquén", "Linares", "Colbún", "Longaví", "Parral", "Retiro",
        "San Javier", "Villa Alegre", "Yerbas Buenas"]),
    ("XVI", "Ñuble", [
        "Chillán", "Bulnes", "Chillán Viejo", "El Carmen", "Pemuco", "Pinto", "Quillón",
        "San Ignacio", "Yungay", "Quirihue", "Cobquecura", "Coelemu", "Ninhue",
        "Portezuelo", "Ránquil", "Treguaco", "San Carlos", "Coihueco", "Ñiquén",
        "San Fabián", "San Nicolás"]),
    ("VIII", "Biobío", [
        "Concepción", "Coronel", "Chiguayante", "Florida", "Hualqui", "Lota", "Penco",
        "San Pedro de la Paz", "Santa Juana", "Talcahuano", "Tomé", "Hualpén", "Lebu",
        "Arauco", "Cañete", "Contulmo", "Curanilahue", "Los Álamos", "Tirúa",
        "Los Ángeles", "Antuco", "Cabrero", "Laja", "Mulchén", "Nacimiento", "Negrete",
        "Quilaco", "Quilleco", "San Rosendo", "Santa Bárbara", "Tucapel", "Yumbel",
        "Alto Biobío"]),
    ("IX", "La Araucanía", [
        "Temuco", "Carahue", "Cunco", "Curarrehue", "Freire", "Galvarino", "Gorbea",
        "Lautaro", "Loncoche", "Melipeuco", "Nueva Imperial", "Padre Las Casas",
        "Perquenco", "Pitrufquén", "Pucón", "Saavedra", "Teodoro Schmidt", "Toltén",
        "Vilcún", "Villarrica", "Cholchol", "Angol", "Collipulli", "Curacautín", "Ercilla",
        "Lonquimay", "Los Sauces", "Lumaco", "Purén", "Renaico", "Traiguén", "Victoria"]),
    ("XIV", "Los Ríos", [
        "Valdivia", "Corral", "Lanco", "Los Lagos", "Máfil", "Mariquina", "Paillaco",
        "Panguipulli", "La Unión", "Futrono", "Lago Ranco", "Río Bueno"]),
    ("X", "Los Lagos", [
        "Puerto Montt", "Calbuco", "Cochamó", "Fresia", "Frutillar", "Los Muermos",
        "Llanquihue", "Maullín", "Puerto Varas", "Castro", "Ancud", "Chonchi",
        "Curaco de Vélez", "Dalcahue", "Puqueldón", "Queilén", "Quellón", "Quemchi",
        "Quinchao", "Osorno", "Puerto Octay", "Purranque", "Puyehue", "Río Negro",
        "San Juan de la Costa", "San Pablo", "Chaitén", "Futaleufú", "Hualaihué", "Palena"]),
    ("XI", "Aysén del General Carlos Ibáñez del Campo", [
        "Coyhaique", "Lago Verde", "Aysén", "Cisnes", "Guaitecas", "Cochrane", "O'Higgins",
        "Tortel", "Chile Chico", "Río Ibáñez"]),
    ("XII", "Magallanes y de la Antártica Chilena", [
        "Punta Arenas", "Laguna Blanca", "Río Verde", "San Gregorio", "Cabo de Hornos",
        "Antártica", "Porvenir", "Primavera", "Timaukel", "Natales", "Torres del Paine"]),
]


def cargar(apps, schema_editor):
    Region = apps.get_model("clientes", "Region")
    Comuna = apps.get_model("clientes", "Comuna")
    for codigo, nombre, comunas in REGIONES:
        region, _ = Region.objects.get_or_create(nombre=nombre, defaults={"codigo": codigo})
        for comuna in comunas:
            Comuna.objects.get_or_create(region=region, nombre=comuna)


class Migration(migrations.Migration):

    dependencies = [("clientes", "0001_initial")]

    operations = [migrations.RunPython(cargar, migrations.RunPython.noop)]
