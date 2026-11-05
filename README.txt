READING LAB — primera interfaz Django

1. Copia analytics/views.py y analytics/urls.py en la carpeta analytics de tu proyecto.
2. Copia analytics/templates/analytics/dashboard.html y analytics/static/analytics/style.css conservando las carpetas.
3. En config/urls.py, añade `include` y la ruta:

   from django.contrib import admin
   from django.urls import path, include
   urlpatterns = [
       path('admin/', admin.site.urls),
       path('', include('analytics.urls')),
   ]

4. Comprueba que 'analytics' aparece en INSTALLED_APPS de config/settings.py.
5. Crea la carpeta private_data junto a manage.py.
6. Copia TU CSV original de Goodreads a private_data/goodreads_library_export.csv.
7. Asegúrate de que private_data/ está en .gitignore.
8. Arranca: python manage.py runserver
9. Abre: http://127.0.0.1:8000/

Esta interfaz lee el CSV local y calcula estadísticas reales. NO modifica models.py ni la base de datos todavía.
No incluyas tu CSV personal en GitHub. La pantalla todavía no incluye controles de usuario, importación ni las vulnerabilidades OWASP, que añadiremos por separado.
