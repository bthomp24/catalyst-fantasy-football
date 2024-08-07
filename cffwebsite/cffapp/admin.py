from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

# admin.site.register(Post)
# admin.site.register(Category)
@admin.register(Post, Category, Player)
class ViewAdmin(ImportExportModelAdmin):
    pass

