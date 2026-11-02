Aqui se explicaran los pasos para inicializar el proyecto (en codificacion)

1ro que nada tienen que instalar docker (https://docs.docker.com/desktop/setup/install/windows-install/)

tienen que tener python preferente de la 3.13 o superior

para ejecutar el docker y ver lo que estan haciendo graficamente es con: docker-compose up --build
y para que deje de ejecutar es con CTRL+C

cuando le muevan a sus models.py (que es la base de datos) en la terminal escriben:
"python manage.py makemigrations" que este hace es cargar como en fila las ediciones de la base de datos,
despues ejecutan:
"python manage.py migrate" que este ya hace los cambios a la base de datos

## Flujo de proyectos

1. Crea una cuenta desde el registro normal e inicia sesión.
2. Cualquier usuario puede crear un proyecto y será el **Técnico QA** de ese proyecto.
3. Desde el detalle del proyecto, su creador puede invitar cuentas existentes como **Desarrolladores**. La opción **Ver proyecto** lleva al dashboard con el checklist, la bitácora de defectos y la matriz de trazabilidad asociados.
4. El rol es por proyecto: una misma persona puede ser Técnico QA de los proyectos que creó y Desarrollador en los proyectos a los que fue invitada.

Checklist y defectos creados dentro de un proyecto quedan asociados a ese proyecto. Para aplicar cambios de esquema en otro entorno, ejecuta `python manage.py migrate`.

Django Admin se mantiene disponible en `/admin/` para tareas administrativas, pero no forma parte de la navegación ni del flujo de pantallas de la aplicación.
