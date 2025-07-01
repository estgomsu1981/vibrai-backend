import os
import re

def create_project_structure(source_file='all_backend_files.txt'):
    """
    Lee un archivo de texto con delimitadores y crea la estructura de
    archivos y carpetas correspondiente.
    """
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: El archivo '{source_file}' no se encontró.")
        print("Asegúrate de que ambos archivos estén en la misma carpeta.")
        return

    # Usamos regex para encontrar todos los bloques de archivos
    file_blocks = re.findall(r'--- START OF FILE (.*?) ---\n(.*?)\n--- END OF FILE .*? ---', content, re.DOTALL)

    if not file_blocks:
        print("Error: No se encontraron bloques de archivos válidos en el archivo fuente.")
        return

    print(f"Encontrados {len(file_blocks)} archivos para crear...")

    for file_path, file_content in file_blocks:
        # Limpiar el nombre del archivo
        file_path = file_path.strip()
        
        # Asegurarse de que los directorios existan
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            print(f"Directorio asegurado: {dir_name}")

        # Escribir el contenido en el archivo
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Quita el último salto de línea si el contenido original no lo tenía
                f.write(file_content.strip())
            print(f"Archivo creado: {file_path}")
        except IOError as e:
            print(f"Error al escribir el archivo {file_path}: {e}")

    print("\n¡Estructura del backend creada con éxito!")
    print("\n--- PRÓXIMOS PASOS ---")
    print("1. Crea un entorno virtual de Python: python -m venv venv")
    print("2. Actívalo:")
    print("   - En Windows: venv\\Scripts\\activate")
    print("   - En macOS/Linux: source venv/bin/activate")
    print("3. Instala las dependencias: pip install -r requirements.txt")
    print("4. Crea un archivo llamado .env y añade tus claves (reemplaza los valores):")
    print('   DATABASE_URL="tu_url_de_la_base_de_datos_de_neon"')
    print('   API_KEY="tu_clave_de_la_api_de_google_ai"')
    print("5. Ejecuta el servidor de desarrollo: uvicorn main:app --reload")

if __name__ == '__main__':
    create_project_structure()