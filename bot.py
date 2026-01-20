import json
from web3 import Web3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================
BOT_TOKEN = "8579124748:AAF2rjNV305KVVgHjtpB9_vBHxTkLMTZwyU"
BASE_RPC = "https://mainnet.base.org"
FACTORY_ADDRESS = Web3.to_checksum_address(
    "0x223Dd4B140A6C5cFb3e732d55B0991BfF952f273"
)

w3 = Web3(Web3.HTTPProvider(BASE_RPC))

with open("abi.json") as f:
    FACTORY_ABI = json.load(f)

factory = w3.eth.contract(
    address=FACTORY_ADDRESS,
    abi=FACTORY_ABI
)

# TEMP SESSION STORAGE (RAM ONLY)
sessions = {}

# ================= UI =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 Import Wallet", callback_data="import")],
        [InlineKeyboardButton("🪙 Create Token", callback_data="create")],
        [InlineKeyboardButton("💰 Buy Token", callback_data="buy")],
        [InlineKeyboardButton("📜 All Tokens", callback_data="list")]
    ])

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐵 *APE CITY LAUNCHPAD*\n\n"
        "Create & buy Base tokens on-chain.\n"
        "⚠️ Use a fresh wallet only.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ================= CALLBACKS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    if query.data == "import":
        sessions[uid] = {}
        await query.message.reply_text(
            "🔑 Send your *PRIVATE KEY* (Base wallet)\n\n"
            "⚠️ Fresh wallet only.",
            parse_mode="Markdown"
        )

    elif query.data == "create":
        if uid not in sessions or "account" not in sessions[uid]:
            await query.message.reply_text("❌ Import wallet first")
            return
        await query.message.reply_text(
            "Send token details in this format:\n\n"
            "`Name,Symbol,MaxSupply`\n\n"
            "Example:\n"
            "`Ape Coin,APE,1000000`",
            parse_mode="Markdown"
        )
        sessions[uid]["action"] = "create"

    elif query.data == "buy":
        if uid not in sessions or "account" not in sessions[uid]:
            await query.message.reply_text("❌ Import wallet first")
            return
        await query.message.reply_text(
            "Send buy order:\n\n"
            "`TokenAddress,ETH_amount`\n\n"
            "Example:\n"
            "`0xABC...,0.01`",
            parse_mode="Markdown"
        )
        sessions[uid]["action"] = "buy"

    elif query.data == "list":
        tokens = factory.functions.getAllTokens().call()
        if not tokens:
            await query.message.reply_text("No tokens yet.")
            return

        msg = "📜 *Ape City Tokens*\n\n"
        for t in tokens:
            msg += f"{t[1]} ({t[2]})\n`{t[0]}`\n\n"

        await query.message.reply_text(msg, parse_mode="Markdown")

# ================= TEXT HANDLER =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text.strip()

    # IMPORT KEY
    if uid in sessions and "account" not in sessions[uid]:
        acct = w3.eth.account.from_key(text)
        sessions[uid]["account"] = acct
        await update.message.reply_text(
            f"✅ Wallet imported\n\n`{acct.address}`",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return

    if uid not in sessions or "action" not in sessions[uid]:
        return

    acct = sessions[uid]["account"]

    # CREATE TOKEN
    if sessions[uid]["action"] == "create":
        name, symbol, supply = text.split(",")
        tx = factory.functions.createToken(
            name.strip(),
            symbol.strip(),
            int(supply.strip())
        ).build_transaction({
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 2_000_000,
            "gasPrice": w3.eth.gas_price
        })
        signed = acct.sign_transaction(tx)
        txh = w3.eth.send_raw_transaction(signed.rawTransaction)
        await update.message.reply_text(
            f"🚀 Token creation sent\n\nTx:\n{txh.hex()}",
            reply_markup=main_menu()
        )

    # BUY TOKEN
    if sessions[uid]["action"] == "buy":
        token, eth = text.split(",")
        tx = factory.functions.buyToken(
            Web3.to_checksum_address(token.strip())
        ).build_transaction({
            "from": acct.address,
            "value": w3.to_wei(eth.strip(), "ether"),
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 500_000,
            "gasPrice": w3.eth.gas_price
        })
        signed = acct.sign_transaction(tx)
        txh = w3.eth.send_raw_transaction(signed.rawTransaction)
        await update.message.reply_text(
            f"💰 Buy order sent\n\nTx:\n{txh.hex()}",
            reply_markup=main_menu()
        )

    sessions[uid].pop("action", None)

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
app.run_polling()
