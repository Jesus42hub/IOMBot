import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "9090025995:AAF_PMO7BqGSMYMb1r1s-rqSVNwsa_fdL0w"

# Esta es la base de datos
def conectar():
    return sqlite3.connect("gastos.db")

def crear_tabla():
    con = conectar()
    con.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            monto REAL NOT NULL,
            descripcion TEXT NOT NULL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()

# ---------- Comandos ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Mi nombre es IOMBot, soy un bot de gastos personales. Usa /ayuda para ver los comandos disponibles.")

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandos disponibles:\n"
        "/start - Inicia el bot\n"
        "/ayuda - Muestra los comandos disponibles\n"
        "/gasto <monto> <descripcion> - Registra un gasto (ej: /gasto 150 tacos)\n"
        "/gastos - Muestra tus últimos 10 gastos\n"
        "/total - Muestra cuánto has gastado en total\n"
        "/borrar <id> - Borra un gasto por su id (ej: /borrar 2)"
    )

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # context.args es la lista de palabras después del comando
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /gasto <monto> <descripcion>\nEjemplo: /gasto 150 tacos")
        return

    try:
        monto = float(context.args[0])
    except ValueError:
        await update.message.reply_text("El monto debe ser un número. Ejemplo: /gasto 150 tacos")
        return

    if monto <= 0:
        await update.message.reply_text("El monto debe ser mayor que 0.")
        return

    descripcion = " ".join(context.args[1:])
    usuario_id = update.effective_user.id

    con = conectar()
    con.execute(
        "INSERT INTO gastos (usuario_id, monto, descripcion) VALUES (?, ?, ?)",
        (usuario_id, monto, descripcion),
    )
    con.commit()
    con.close()

    await update.message.reply_text(f"Gasto registrado: ${monto:.2f} - {descripcion}")

async def gastos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id

    con = conectar()
    filas = con.execute(
        "SELECT id, monto, descripcion, fecha FROM gastos "
        "WHERE usuario_id = ? ORDER BY id DESC LIMIT 10",
        (usuario_id,),
    ).fetchall()
    con.close()

    if not filas:
        await update.message.reply_text("Aún no tienes gastos registrados.")
        return

    texto = "Tus últimos gastos:\n"
    for id_, monto, desc, fecha in filas:
        texto += f"#{id_} | ${monto:.2f} | {desc} | {fecha[:10]}\n"
    await update.message.reply_text(texto)

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id

    con = conectar()
    resultado = con.execute(
        "SELECT SUM(monto) FROM gastos WHERE usuario_id = ?", (usuario_id,)
    ).fetchone()[0]
    con.close()

    resultado = resultado or 0
    await update.message.reply_text(f"Has gastado en total: ${resultado:.2f}")

async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Uso: /borrar <id>\nEjemplo: /borrar 2")
        return

    gasto_id = int(context.args[0])
    usuario_id = update.effective_user.id

    con = conectar()
    cursor = con.execute(
        "DELETE FROM gastos WHERE id = ? AND usuario_id = ?",
        (gasto_id, usuario_id),
    )
    con.commit()
    borrados = cursor.rowcount
    con.close()

    if borrados:
        await update.message.reply_text(f"Gasto #{gasto_id} borrado.")
    else:
        await update.message.reply_text("No encontré un gasto tuyo con ese id.")

# ---------- Inicio ----------
crear_tabla()

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ayuda", ayuda))
app.add_handler(CommandHandler("gasto", gasto))
app.add_handler(CommandHandler("gastos", gastos))
app.add_handler(CommandHandler("total", total))
app.add_handler(CommandHandler("borrar", borrar))
app.run_polling()