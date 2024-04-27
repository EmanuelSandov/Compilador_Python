import re
from enum import Enum

nombre_archivo = 'pruebas.txt'

variables_declaradas = set()

class TipoToken(Enum):
    PalRes = 1
    Identificador = 2
    CaracEsp = 3
    PuntoComa = 4
    CaracEspIn = 5
    CaracEspFi = 6
    COMENTARIO = 7
    No = 8
    CADENA = 9
    DESCONOCIDO = 10

# Expresiones regulares para identificar patrones
patron_asignacion = r'(\w+)\s*=\s*([0-9]+|[a-zA-Z_]\w*)'
patron_declaracion = r'\b(\w+)\b\s*(=\s*\w+)?;'
patron_operacion = r'(\w+)\s*=\s*([a-zA-Z_]\w*)\s*([+\-*/])\s*([a-zA-Z_]\w*|[0-9]+)'
patron_caracter_especial = r'[()[\]{}]'
patron_punto_coma = r';'

# Funciones para verificación de cadenas y caracteres
def es_palabra_reservada(palabra):
    palabras_reservadas = {
        "if", "else", "while", "for", "int", "float", "char", "return", "bool",
        "const", "true", "false", "break", "main", "cout", "endl", "void", "switch", "case",
        "default", "cin"
    }
    return palabra in palabras_reservadas

def es_numero(palabra):
    return all(caracter.isdigit() or caracter == '.' for caracter in palabra)

def es_caracter_especial_apertura(caracter):
    caracteres_especiales_apertura = "[({"
    return caracter in caracteres_especiales_apertura

def es_caracter_especial_cierre(caracter):
    caracteres_especiales_cierre = "])}"
    return caracter in caracteres_especiales_cierre

def es_caracter_especial(caracter):
    caracteres_especiales = "!''@#$%<>^&*-+=:,.?/"
    return caracter in caracteres_especiales

def es_caracter_punto_coma(caracter):
    return caracter == ";"

# Función para procesar las asignaciones
def procesar_asignaciones(asignaciones):
    variables = {}
    for asignacion in asignaciones:
        variable, valor = asignacion
        variables[variable] = int(valor) if valor.isdigit() else variables.get(valor, 0)
    return variables

    DESCONOCIDO = 10

mensajes_cout = []  # Lista para guardar los mensajes de cout

def procesar_impresion(linea, variables):
    partes = linea.split("<<")
    mensaje = ""
    for parte in partes:
        parte = parte.strip()
        if parte in ["cout", "endl", "endl;"]:
            continue
        if parte.startswith('"') and parte.endswith('"'):
            mensaje += parte[1:-1] + " "
        elif parte in variables:
            mensaje += str(variables[parte]) + " "

    if mensaje:
        mensajes_cout.append(mensaje.strip())

def obtener_bloque_for(lineas_codigo, indice_inicio):
    if "{" in lineas_codigo[indice_inicio]:
        indice_abre = indice_inicio
        contador_llaves = 1
        indice_cierra = indice_abre + 1

        while indice_cierra < len(lineas_codigo) and contador_llaves > 0:
            if '{' in lineas_codigo[indice_cierra]:
                contador_llaves += 1
            if '}' in lineas_codigo[indice_cierra]:
                contador_llaves -= 1
            indice_cierra += 1

        cuerpo_for = lineas_codigo[indice_abre + 1:indice_cierra]
        return cuerpo_for, indice_cierra

    else:
        # Si no se encuentran llaves, devuelve un error
        return None, None

def analizar_lexico(codigo):
    tokens = []
    palabra_actual = ""
    en_comentario_bloque = False
    comentario_actual = ""
    en_cadena = False
    cadena_actual = ""

    i = 0
    while i < len(codigo):
        caracter = codigo[i]
        
        if en_comentario_bloque:
            comentario_actual += caracter
            if i < len(codigo) - 1 and codigo[i] == '*' and codigo[i + 1] == '/':
                en_comentario_bloque = False
                comentario_actual += '/'
                tokens.append((comentario_actual, TipoToken.COMENTARIO))
                comentario_actual = ""
                i += 1
                continue
            i += 1
            continue

        elif not en_comentario_bloque and i < len(codigo) - 1 and codigo[i] == '/' and codigo[i + 1] == '*':
            en_comentario_bloque = True
            comentario_actual = "/*"
            i += 1
            continue

        if caracter == '"' and not en_cadena:
            en_cadena = True
            cadena_actual += caracter
            i += 1
            continue

        if en_cadena:
            cadena_actual += caracter
            if caracter == '"':
                en_cadena = False
                tokens.append((cadena_actual, TipoToken.CADENA))
                cadena_actual = ""
            i += 1
            continue

        if not en_comentario_bloque and not en_cadena and i < len(codigo) - 1 and codigo[i] == '/' and codigo[i + 1] == '/':
            while i < len(codigo) and codigo[i] != '\n':
                i += 1
            i += 1
            continue

        if caracter.isalnum() or caracter == '_':
            palabra_actual += caracter
        else:
            if palabra_actual:
                if es_palabra_reservada(palabra_actual):
                    tokens.append((palabra_actual, TipoToken.PalRes))
                elif es_numero(palabra_actual):
                    tokens.append((palabra_actual, TipoToken.No))
                else:
                    tokens.append((palabra_actual, TipoToken.Identificador))
                palabra_actual = ""

            if es_caracter_especial(caracter):
                tokens.append((caracter, TipoToken.CaracEsp))
            elif es_caracter_punto_coma(caracter):
                tokens.append((caracter, TipoToken.PuntoComa))
            elif es_caracter_especial_apertura(caracter):
                tokens.append((caracter, TipoToken.CaracEspIn))
            elif es_caracter_especial_cierre(caracter):
                tokens.append((caracter, TipoToken.CaracEspFi))
        i += 1
    
    return tokens

def token_type_to_regex(tipo):
    tipos_regex = {
        TipoToken.PalRes: "PalRes",
        TipoToken.Identificador: "Identificador",
        TipoToken.CaracEsp: "CaracEsp",
        TipoToken.PuntoComa: "PuntoComa",
        TipoToken.CaracEspIn: "CaracEspIn",
        TipoToken.CaracEspFi: "CaracEspFi",
        TipoToken.CADENA: "CADENA",
        TipoToken.COMENTARIO: "COMENTARIO",
        TipoToken.No: "No",
        TipoToken.DESCONOCIDO: "DESCONOCIDO"
    }

    return tipos_regex.get(tipo, "DESCONOCIDO") 
# Función para analizar una línea
def analizar_linea(linea):
    tokens = []
    if re.match(patron_asignacion, linea):
        tokens.append("PalRes Identificador CaracEsp No PuntoComa")
    elif re.match(patron_declaracion, linea):
        tokens.append("PalRes Identificador PuntoComa")
    elif re.match(r'^\s*$', linea):
        tokens.append("")
    else:
        tokens.append("No Coincide")

    return tokens
# Función para procesar las operaciones
def procesar_operaciones(operaciones, variables):
    for operacion in operaciones:
        variable, var1, operador, var2 = operacion
        if operador == '+':
            variables[variable] = variables.get(var1, 0) + variables.get(var2, 0)
        elif operador == '-':
            variables[variable] = variables.get(var1, 0) - variables.get(var2, 0)
        elif operador == '*':
            variables[variable] = variables.get(var1, 0) * variables.get(var2, 0)
        elif operador == '/':
            variables[variable] = variables.get(var1, 0) / variables.get(var2, 0)
    return variables

def manejar_declaracion_variable(tokens):
    for token, tipo in tokens:
        if tipo == TipoToken.Identificador:
            variables_declaradas.add(token)
            print(f"Variable declarada: {token}")  # Mensaje de depuración
            
def evaluar_expresion(expresion, variables):
    # Esta función evalúa expresiones aritméticas simples.
    partes = expresion.split()
    if len(partes) == 1:
        return int(partes[0]) if partes[0].isdigit() else variables.get(partes[0], 0)
    elif len(partes) == 3:
        op1, operador, op2 = partes
        op1 = int(op1) if op1.isdigit() else variables.get(op1, 0)
        op2 = int(op2) if op2.isdigit() else variables.get(op2, 0)
        if operador == '+':
            return op1 + op2
        # Aquí puedes agregar más operadores si es necesario
    return 0  # Valor por defecto si la expresión no puede evaluarse

solicitudes_cin = []  
contador_corchetes = 0

def ejecutar_linea(linea, variables):
    tokens = analizar_lexico(linea)
    
    if "for" in linea:
        return  # Ignora las líneas que contienen un bucle 'for'
    
    if 'cout' in linea:
        partes = linea.split('<<')
        mensaje = ""
        for parte in partes[1:]:  # Ignora la primera parte ("cout") ya que no se necesita
            parte = parte.strip().strip(';')  # Quita los espacios y los posibles puntos y comas al final
            if parte == "endl":
                continue  # Ignora 'endl'
            if parte.startswith('"') and parte.endswith('"'):
                # Esto es un literal de cadena
                mensaje += parte[1:-1]  # Imprime el literal sin las comillas
            else:
                # Esto es una variable
                mensaje += str(variables.get(parte, parte))  # Imprime el valor de la variable o su nombre si no está definida
        print(mensaje)  # Imprime el mensaje compilado
        return
    
    if not tokens:
        return  # Si no hay tokens, no hay nada que procesar

    # Comprobando si la línea tiene una asignación
    if any(token == "=" for token, _ in tokens):
        var_name, _, valor = linea.partition('=')
        var_name = var_name.strip()
        valor = valor.strip().strip(';')  # Quitar los posibles espacios y puntos y comas al final

        # Manejando las diferentes situaciones de asignación
        if valor.isdigit():
            variables[var_name] = int(valor)
        elif any(op in valor for op in {'+', '-', '*', '/'}): 
            for variable in variables:
                valor = valor.replace(variable, str(variables[variable]))
            variables[var_name] = eval(valor)
        elif valor in variables:
            variables[var_name] = variables[valor]
        else:
            valor_evaluado = evaluar_expresion(valor, variables)
            variables[var_name] = valor_evaluado
            
        print(f"Variables después de ejecutar '{linea}': {variables}")
    
    return variables

def ejecutar_impresion(linea, variables):
    # Esto es un ejemplo básico y puede necesitar más lógica para manejar diferentes casos
    if "cout" in linea:
        linea = linea.replace('<<', ' << ')
        partes = linea.split()
        partes = [p.strip() for p in partes if p.strip() and p.strip() != "endl" and p.strip() != "cout"]
        partes_impresion = []
    for parte in partes:
     if parte.startswith('"') and parte.endswith('"'):
        # Esto es un literal de cadena
        parte_limpia = parte[1:-1]
        partes_impresion.append(parte_limpia)
    else:
        # Esto es una variable
        partes_impresion.append(str(variables.get(parte, parte)))
        print(" ".join(partes_impresion))

def analizarSintaxis(linea):
    tokens = analizar_lexico(linea)
    tokensStr = " ".join(token_type_to_regex(tipo) for _, tipo in tokens)

    print(f"Cadena de Tokens para la línea: '{linea}' es '{tokensStr}'")  # Agregar para depuración
    
     # Procesar declaraciones de variables
    if any(tipo == TipoToken.PalRes and token in ['int', 'float', 'char'] for token, tipo in tokens):
        print("Posible declaración de variable encontrada.")  # Mensaje de depuración
        manejar_declaracion_variable(tokens)

    # Verificar si las variables utilizadas están declaradas
    for token, tipo in tokens:
        if tipo == TipoToken.Identificador and token not in variables_declaradas:
            print(f"Error: Variable '{token}' no declarada.")
            exit()  # Terminar el programa

    # Procesar ciclos for
    if 'for' in tokensStr:
        # Extraer la inicialización del ciclo for
        inicio_for = linea.find('(') + 1
        fin_for = linea.find(';')
        inicializacion_for = linea[inicio_for:fin_for]
        partes_for = re.findall(r'\b\w+\b', inicializacion_for)
        
        # Verificar si la variable del ciclo for está declarada
        if partes_for and not es_numero(partes_for[0]):
            variable_for = partes_for[0].split('=')[0].strip()
            if variable_for not in variables_declaradas:
                return f"Error: Variable '{variable_for}' no declarada antes de su uso en el ciclo for."


    if len(tokens)<0 :  # Verificar si hay al menos 54 tokens
        return "Linea en Blanco"
    # Definición de patrones específicos
    patron1 = re.compile(r'^PalRes\sIdentificador\s*CaracEsp\s*No\s*PuntoComa$')  # int variable=1;
    patron2 = re.compile(r'^PalRes\sIdentificador\s*PuntoComa$')  # int a;
    patron3 = re.compile(r'^PalRes\sIdentificador(\s*CaracEsp\sIdentificador)*\sPuntoComa$')  # int a,v,,f,f,d,...;
    patron4 = re.compile(r'^PalRes\sPalRes\s*CaracEspIn\s*CaracEspFi\s*CaracEspIn$')  # Funcion
    patron5 = re.compile(r'^\s*CaracEspFi\s*')  # } del final
    patron6 = re.compile(r'^\s*$')  # LINEA EN BLANCO
    patron7 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*PalRes\sIdentificador\s*CaracEspFi\s*PuntoComa\s')
    patron8 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*PalRes\sIdentificador\s*CaracEspFi\s*PuntoComa\s')
    patron9 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*PalRes\sIdentificador(\s*CaracEsp\s*PalRes\sIdentificador\s*)*CaracEspFi\s*PuntoComa\s')
    patron10 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*Identificador(\s*CaracEsp\s*Identificador\s*)*CaracEspFi\s*PuntoComa\s')
    patron11 = re.compile(r'^PalRes\sPalResCaracEspIn\s*PalRes\sIdentificador\s*CaracEspFi\s*CaracEspIn\s')
    patron12 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*PalRes\sIdentificador(\s*CaracEsp\s*PalRes\sIdentificador\s*)*CaracEspFi\s*CaracEspIn\s')
    patron13 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*Identificador(\s*CaracEsp\s*Identificador\s*)*CaracEspFi\s*CaracEspIn\s')
    patron14 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*CaracEspFi\s*PuntoComa\s')
    patron15 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*(PalRes\sIdentificador(\s*CaracEsp\s*PalRes\sIdentificador)*)?\s*CaracEspFi\s*CaracEspIn\s*.*\s*CaracEspFi$')
    patron16 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*PalRes\s*CaracEsp\s*Identificador(\s*CaracEsp\s*PalRes\s*CaracEsp\s*Identificador)*\s*CaracEspFi\s*PuntoComa$')
    patron17 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*PalRes\s*Identificador\s*CaracEsp\s*No(\s*CaracEsp\s*PalRes\s*Identificador\s*CaracEsp\s*No)*\s*CaracEspFi\s*PuntoComa$')
    patron18 = re.compile(r'^PalRes\sIdentificador\s*CaracEspIn\s*(PalRes\sIdentificador(\s*CaracEsp\s*PalRes\sIdentificador)*)?\s*CaracEspFi\s*PalRes\s*PuntoComa\s')
    patron19 = re.compile(r'^Identificador\s*CaracEsp\s*(No|Identificador)\s*PuntoComa$')
    patron20 = re.compile(r'^PalRes\s*CaracEspIn\s*(Identificador|No)\s*CaracEsp\s*(CaracEsp)?\s*(Identificador|No)\s*CaracEspFi\s*CaracEspIn$')
    patron21 = re.compile(r'^CaracEspFi\s*PalRes\s*CaracEspIn$')
    patron22 = re.compile(r'^PalRes\s*CaracEspIn\s*Identificador\s*CaracEsp\s*No\s*PuntoComa\s*(Identificador|No)\s*CaracEsp\s*(CaracEsp\s*)?(Identificador|No)\s*PuntoComa\s*Identificador\s*CaracEsp\s*(CaracEsp\s*)?CaracEspFi\s*CaracEspIn$')
    patron23 = re.compile(r'^PalRes\s*Identificador\s*CaracEspIn\s*No\s*CaracEspFi\s*PuntoComa$')
    patron24 = re.compile(r'^PalRes\s*CaracEsp\s*Identificador\s*PuntoComa$')
    patron25 = re.compile(r'^PalRes\s*Identificador\s*CaracEsp\s*(Identificador|No)\s*PuntoComa$')
    patron26 = re.compile(r'^PalRes\s*(Identificador|No)\s*PuntoComa$')
    patron27 = re.compile(r'^Identificador\s*CaracEspIn\s*CaracEspFi\s*PuntoComa$')
    patron28 = re.compile(r'^Identificador\s*CaracEspIn\s*(Identificador|No)(\s*CaracEsp\s*(Identificador|No))*\s*CaracEspFi\s*PuntoComa$')
    patron29 = re.compile(r'^Identificador\s*CaracEsp\s*CaracEsp\s*PuntoComa$')
    patron30 = re.compile(r'^COMENTARIO$')
    patron31 = re.compile(r'^PalRes\s+CaracEsp\s+CaracEsp\s+CADENA\s+PuntoComa$')
    patron32 = re.compile(r'^Identificador\s*CaracEsp\s*CaracEsp\s*Identificador\s*PuntoComa$')
    patron33 = re.compile(r'^PalRes\s*CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*Identificador\s*((CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*Identificador\s*)*)?CaracEsp\s*CaracEsp\s*PalRes\s*PuntoComa$')
    patron34 = re.compile(r'^PalRes\s*PalRes\s*CaracEspIn\s*CaracEspFi\s*PuntoComa$')
    patron35 = re.compile(r'^PalRes\s*CaracEspIn\s*Identificador\s*CaracEsp\s*No\s*PuntoComa\s*(Identificador|No)\s*CaracEsp\s*(CaracEsp\s*)?(Identificador|No)\s*PuntoComa\s*Identificador\s*CaracEsp\s*(CaracEsp\s*)?CaracEspFi$')
    patron36 = re.compile(r'^PalRes\s*CaracEspIn\s*PalRes\s*Identificador\s*CaracEsp\s*No\s*PuntoComa\s*(Identificador|No)\s*CaracEsp\s*(CaracEsp\s*)?(IdentificadorD|No)\s*PuntoComa\s*Identificador\s*CaracEsp\s*(CaracEsp\s*)?CaracEspFi$')
    patron37 = re.compile(r'^PalRes\s+CaracEspIn\s+PalRes\s+Identificador\s+CaracEsp\s+No\s+((CaracEsp\s+Identificador\s+CaracEsp\s+No\s+)*)?PuntoComa\s+Identificador\s+CaracEsp\s+No\s+PuntoComa\s+Identificador\s+CaracEsp\s+CaracEsp\s+((CaracEsp\s+Identificador\s+CaracEsp\s+CaracEsp\s+)*)?CaracEspFi$')
    patron38 = re.compile(r'^PalRes\s*CaracEspIn\s*PuntoComa\s*PuntoComa\s*CaracEspFi$')
    patron39 = re.compile(r'^PalRes\s*Identificador\s*CaracEsp\s*PalRes\s*PuntoComa$')
    patron40 = re.compile(r'^PalRes\s*CaracEspIn\s*CaracEsp\s*Identificador\s*CaracEspFi\s*CaracEspIn$')
    patron41 = re.compile(r'^PalRes\s*CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*PalRes\s*PuntoComa$')
    patron42 = re.compile(r'^PalRes\s*CaracEspIn\s*Identificador\s*CaracEspFi\s*CaracEspIn$')
    patron43 = re.compile(r'^PalRes\s*No\s*CaracEsp$')
    patron44 = re.compile(r'^PalRes\s*PuntoComa$')
    patron45 = re.compile(r'^Identificador\s*CaracEsp\s*PalRes\s*PuntoComa$')
    patron46 = re.compile(r'^PalRes\s*CaracEsp$')
    patron47 = re.compile(r'^PalRes\s*Identificador\s*CaracEspIn\s*CaracEspFi\s*CaracEsp\s*CADENA\s*PuntoComa$')
    patron48 = re.compile(r'^PalRes\s*CaracEspIn\s*PalRes\s*Identificador\s*CaracEsp\s*No\s*PuntoComa\s*Identificador\s*CaracEspIn\s*Identificador\s*CaracEspFi\s*PuntoComa\s*Identificador\s*CaracEsp\s*CaracEsp\s*CaracEspFi\s*CaracEspIn$')
    patron49 = re.compile(r'^PalRes\s*CaracEspIn\s*Identificador\s*CaracEspIn\s*Identificador\s*CaracEspFi\s*CaracEspFi\s*CaracEspIn$')
    patron50 = re.compile(r'^PalRes\s*CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*Identificador\s*CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*Identificador\s*CaracEspIn\s*Identificador\s*CaracEspFi\s*CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*PalRes\s*PuntoComa$')
    patron51 = re.compile(r'^PalRes\s*Identificador\s*CaracEspIn\s*PalRes\s*Identificador\s*CaracEspFi\s*CaracEspIn')
    patron52 = re.compile(r'^PalRes\s*CaracEspIn\s*Identificador\s*CaracEspIn\s*Identificador\s*CaracEspFi\s*CaracEsp\s*Identificador\s*CaracEspIn\s*Identificador\s*CaracEsp\s*No\s*CaracEspFi\s*CaracEspFi$')
    patron53 = re.compile(r'^PalRes\s*CaracEspIn\s*Identificador\s*CaracEspIn\s*Identificador\s*CaracEspFi\s*CaracEsp\s*Identificador\s*CaracEspIn\s*Identificador\s*CaracEsp\s*No\s*CaracEspFi\s*CaracEsp\s*CaracEsp\s*Identificador\s*CaracEspIn\s*Identificador\s*CaracEspFi\s*CaracEsp\s*CaracEsp\s*Identificador\s*CaracEspIn\s*No\s*CaracEspFi\s*CaracEspFi$')
    patron54 = re.compile(r'^s*CaracEspIn$')
    patron55 = re.compile(r'^PalRes\s*Identificador\s*CaracEspIn\s*CaracEspFi\s*PuntoComa$')
    patron56 = re.compile(r'^PalRes\s*CaracEspIn\s*Identificador\s*CaracEsp\s*CaracEsp\s* No\s*PuntoComa\s*Identificador\s*CaracEsp\s*CaracEsp\s*No\s*PuntoComa\s*Identificador\s*CaracEsp\s*CaracEsp\s*CaracEspFi\s*CaracEspIn\s*')
    patron57 = re.compile(r'^PalRes\s*CaracEspIn\s*PalRes\s*Identificador\s*CaracEsp\s*No\s*PuntoComa\s*Identificador\s*CaracEsp\s*No\s*PuntoComa\s*Identificador\s*CaracEsp\s*CaracEsp\s*CaracEspFi\s*CaracEspIn')
    patron58 = re.compile(r'^Identificador\s*CaracEsp\s*Identificador\s*CaracEsp\s*No\s*PuntoComa')
    patron59 = re.compile(r'^PalRes\s*CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*Identificador\s*CaracEspIn\s*Identificador\s*CaracEspFi\s*CaracEsp\s*CaracEsp\s*PalRes\s*PuntoComa')
    patron60 = re.compile(r'^PalRes\s*CaracEspIn\s*Identificador\s*CaracEsp\s*CaracEsp\s*No\s*PuntoComa\s*Identificador\s*CaracEsp\s*No\s*PuntoComa\s*Identificador\s*CaracEsp\s*CaracEsp\s*CaracEspFi\s*CaracEspIn')
    patron61 = re.compile(r'^Identificador\s*CaracEsp')
    patron62= re.compile(r'^PalRes\s*CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*Identificador\s*CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*PalRes\s*PuntoComa')
    patron63= re.compile(r'^PalRes\s*CaracEsp\s*CaracEsp\s*Identificador\s*PuntoComa')
    patron64= re.compile(r'^PalRes\s*CaracEsp\s*CaracEsp\s*Identificador\s*CaracEspIn\s*Identificador\s*CaracEspFi\s*PuntoComa')
    patron65= re.compile(r'^PalRes\s*CaracEsp\s*CaracEsp\s*Identificador\s*CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*Identificador\s*CaracEsp\s*CaracEsp\s*CADENA\s*CaracEsp\s*CaracEsp\s*Identificador\s*CaracEsp\s*Identificador\s*CaracEsp\s*CaracEsp\s*PalRes\s*PuntoComa')

    if patron1.match(tokensStr):
        return "Correcta",
    elif patron2.match(tokensStr):
        return "Correcta",
    elif patron3.match(tokensStr):
        return "Correcta",
    elif patron4.match(tokensStr):
        return "Correcta",
    elif patron5.match(tokensStr):
        return "Correcta",
    elif patron6.match(tokensStr):
        return "Texto Vacio",
    elif patron7.match(tokensStr):
        return "Correcta",
    elif patron8.match(tokensStr):
        return "Correcta",
    elif patron9.match(tokensStr):
        return "Correcta",
    elif patron10.match(tokensStr):
        return "Correcta",
    elif patron11.match(tokensStr):
        return "Correcta",
    elif patron12.match(tokensStr):
        return "Correcta",
    elif patron13.match(tokensStr):
        return "Correcta",
    elif patron14.match(tokensStr):
        return "Correcta",
    elif patron15.match(tokensStr):
        return "Correcta",
    elif patron16.match(tokensStr):
        return "Correcta",
    elif patron17.match(tokensStr):
        return "Correcta",
    elif patron18.match(tokensStr):
        return "Correcta",
    elif patron19.match(tokensStr):
        return "Correcta", 
    elif patron20.match(tokensStr):
        return "Correcta",
    elif patron21.match(tokensStr):
        return "Correcta",
    elif patron22.match(tokensStr):
        return "Correcta",
    elif patron23.match(tokensStr):
        return "Correcta",
    elif patron24.match(tokensStr):
        return "Correcta",
    elif patron25.match(tokensStr):
        return "Correcta",
    elif patron26.match(tokensStr):
        return "Correcta", 
    elif patron27.match(tokensStr):
        return "Correcta",
    elif patron28.match(tokensStr):
        return "Correcta",
    elif patron29.match(tokensStr):
        return "Correcta",
    elif patron30.match(tokensStr):
        return "Correcta",
    elif patron31.match(tokensStr):
        return "Correcta",
    elif patron32.match(tokensStr):
        return "Correcta",
    elif patron33.match(tokensStr):
        return "Correcta",
    elif patron34.match(tokensStr):
        return "Correcta",
    elif patron35.match(tokensStr):
        return "Correcta",
    elif patron36.match(tokensStr):
        return "Correcta", 
    elif patron37.match(tokensStr):
        return "Correcta",
    elif patron38.match(tokensStr):
        return "Correcta",
    elif patron39.match(tokensStr):
        return "Correcta", 
    elif patron40.match(tokensStr):
        return "Correcta",
    elif patron41.match(tokensStr):
        return "Correcta",
    elif patron42.match(tokensStr):
        return "Correcta",
    elif patron43.match(tokensStr):
        return "Correcta",
    elif patron44.match(tokensStr):
        return "Correcta", 
    elif patron45.match(tokensStr):
        return "Correcta",
    elif patron46.match(tokensStr):
        return "Correcta",
    elif patron47.match(tokensStr):
        return "Correcta",
    elif patron48.match(tokensStr):
        return "Correcta",
    elif patron49.match(tokensStr):
        return "Correcta", 
    elif patron50.match(tokensStr):
        return "Correcta",
    elif patron51.match(tokensStr):
        return "Correcta",
    elif patron52.match(tokensStr):
        return "Correcta", 
    elif patron53.match(tokensStr):
        return "Correcta",
    elif patron54.match(tokensStr):
        return "Correcta",
    elif patron55.match(tokensStr):
        return "Correcta"
    elif patron56.match(tokensStr):
        return "Correcta"
    elif patron57.match(tokensStr):
        return "Correcta"
    elif patron58.match(tokensStr):
        return "Correcta"
    elif patron59.match(tokensStr):
        return "Correcta"
    elif patron60.match(tokensStr):
        return "Correcta"
    elif patron61.match(tokensStr):
        return "Correcta"
    elif patron62.match(tokensStr):
        return "Correcta"
    elif patron63.match(tokensStr):
        return "Correcta"
    elif patron64.match(tokensStr):
        return "Correcta"
    elif patron65.match(tokensStr):
        return "Correcta"
    elif patron6.match(tokensStr):
        return "Correcta"
    elif patron6.match(tokensStr):
        return "Correcta"
    else:
        return "SYNTAX ERROR"
    
fin_codigo_fuente = "// FIN DEL CODIGO"
# Leer el código fuente desde el archivo externo
with open(nombre_archivo, 'r') as archivo:
    lineas_codigo = archivo.readlines()

# Analizar el código línea por línea
texto_analizado = "\nAnálisis línea por línea:\n\n"
error_encontrado = False
error_encontrado1= False
variables ={}
for i, linea in enumerate(lineas_codigo):
    # Detener el análisis si se llega al final del código fuente
    if fin_codigo_fuente in linea:
        break

    contador_corchetes += linea.count('{')
    contador_corchetes -= linea.count('}')
    if "for" in linea:
        print(f"Entrando en bucle 'for': {linea.strip()}")

        # Expresión regular ajustada para capturar ambos casos
        match = re.search(
            r"for\s*\(\s*(int\s+)?([a-z])\s*=\s*([0-9]+)\s*;\s*\2\s*(<|>|<=|>=)\s*([0-9]+)\s*;\s*\2(\+\+|--)\s*\)",
            linea
        )

        if match:
            declaracion_int, var_bucle, valor_inicial, operador_comparacion, valor_final, operador_bucle = match.groups()
            valor_inicial, valor_final = int(valor_inicial), int(valor_final)

            if declaracion_int:
                # Si la variable se declara dentro del bucle, se agrega a las variables declaradas
                variables_declaradas.add(var_bucle)

            variables[var_bucle] = valor_inicial

            # Definir la condición del bucle y el cambio de la variable del bucle
            if operador_comparacion in ["<=", "<"]:
                condicion = lambda v: v < valor_final if operador_comparacion == "<" else v <= valor_final
                incremento = 1
            elif operador_comparacion in [">=", ">"]:
                condicion = lambda v: v > valor_final if operador_comparacion == ">" else v >= valor_final
                incremento = -1
            else:
                print(f"Operador de comparación no reconocido: {operador_comparacion}")
                error_encontrado = True
                break

            # Verificación de coherencia para evitar bucles infinitos
            condicion_infinita = False
            if operador_bucle == "++":
                if (operador_comparacion in ["<", "<="] and valor_inicial >= valor_final) or \
                   (operador_comparacion in [">", ">="]):
                    condicion_infinita = True
            elif operador_bucle == "--":
                if (operador_comparacion in [">", ">="] and valor_inicial <= valor_final) or \
                   (operador_comparacion in ["<", "<="]):
                    condicion_infinita = True

            if condicion_infinita:
                print("Error lógico: el bucle 'for' puede resultar en un ciclo infinito.")
                error_encontrado = True
                break

            # Obtener el cuerpo del bucle
            cuerpo_for, fin_for = obtener_bloque_for(lineas_codigo, i)
             # Verifica si se encontraron las llaves del bucle for
            if cuerpo_for is None and fin_for is None:
             print(f"Error: Bucle 'for' sin llaves en la línea {i}.")
             error_encontrado = True
             break
            # Ejecutar el bucle
            while condicion(variables[var_bucle]):
                for linea_for in cuerpo_for:
                    if "cout" in linea_for:
                        procesar_impresion(linea_for, variables)
                    else:
                        ejecutar_linea(linea_for, variables)
                variables[var_bucle] += incremento
            print(f"Saliendo de bucle 'for', {var_bucle} = {variables[var_bucle]}")

            i = fin_for - 1  # Salta al final del bloque for

        else:
            print(f"Error: Bucle 'for' mal estructurado en la línea {i}.")
            error_encontrado = True
            break  # Termina el análisis debido al error

        continue  # Salta al final del bloque for, evitando la reiteración
    
    if "cin" in linea:
        variable = linea.split(">>")[1].strip().strip(';')
        valor = input(f'Ingrese un valor para {variable}: ')
        valor = int(valor) if valor.isdigit() else valor  
        variables[variable] = valor
        mensajes_cout.append(f' {valor}')  # Guardar mensaje de cin
        continue  # Continúa con la siguiente línea después de manejar cin
    # Manejo de línea regular
    if "cout" in linea:
        procesar_impresion(linea, variables)
    elif "cin" in linea:
        ejecutar_linea(linea, variables)
    else:
        ejecutar_linea(linea, variables)

    # Analizar sintaxis y otros procesos
    resultado_sintaxis = analizarSintaxis(linea)
    texto_analizado += f"Línea {i}: {linea.strip()} - {resultado_sintaxis}\n"
    if resultado_sintaxis == "SYNTAX ERROR":
        print(f"Error de sintaxis encontrado en la línea {i}. Terminando análisis.")
        error_encontrado = True
        break
if error_encontrado:
    exit()
if contador_corchetes != 0:
    print(f"Error: Corchetes desbalanceados. {'Faltan' if contador_corchetes > 0 else 'Sobran'} {abs(contador_corchetes)} corchete(s).")
    error_encontrado1 = True
if error_encontrado1:
    exit()
# Si se encontró un error, no continuar con el procesamiento
# Convertir el diccionario de variables a texto
texto_resultado = "\nResultados:\n"
variables = {}
for variable, valor in variables.items():
    texto_resultado += f"{variable} = {valor}\n"

# Anexar los resultados al final del archivo original
with open(nombre_archivo, 'a') as archivo:
    archivo.write(texto_resultado)
    archivo.write("\n")  # Agrega una línea en blanco para separar el resultado del código

print("                        CODIGO EJECUTADO              ")
for mensaje in mensajes_cout:
    print(mensaje)
