// Ape City Telegram Launchpad Bot // FULL WORKING VERSION (Buttons + Base Contract) // Node.js v18+, ethers v6, no external APIs

import TelegramBot from "node-telegram-bot-api"; import { ethers } from "ethers"; import dotenv from "dotenv";

dotenv.config();

// ================= CONFIG ================= const BOT_TOKEN = process.env.BOT_TOKEN; const BASE_RPC = process.env.BASE_RPC_URL || "https://mainnet.base.org"; const FACTORY_ADDRESS = "0x223Dd4B140A6C5cFb3e732d55B0991BfF952f273";

if (!BOT_TOKEN) { console.error("❌ BOT_TOKEN missing"); process.exit(1); }

// ================= ABI ================= const FACTORY_ABI = [ "function createToken(string name,string symbol,uint256 maxSupply) returns (address)", "function buyToken(address tokenAddress) payable", "function BASE_PRICE() view returns (uint256)", "function getAllTokens() view returns (tuple(address token,string name,string symbol)[])" ];

// ================= BOT ================= const bot = new TelegramBot(BOT_TOKEN, { polling: true }); const provider = new ethers.JsonRpcProvider(BASE_RPC);

// userId => wallet const userWallets = {};

console.log("✅ Ape City Bot running...");

// ================= START ================= bot.onText(//start/, (msg) => { bot.sendMessage(msg.chat.id, "🏙️ Welcome to Ape City\nBase Token Launchpad", { parse_mode: "Markdown", reply_markup: { inline_keyboard: [ [{ text: "🔑 Import Wallet", callback_data: "import_wallet" }], [{ text: "🚀 Create Token", callback_data: "create_token" }], [{ text: "💰 Buy Token", callback_data: "buy_token" }], [{ text: "📊 List Tokens", callback_data: "list_tokens" }] ] } }); });

// ================= BUTTON HANDLER ================= bot.on("callback_query", async (query) => { const chatId = query.message.chat.id; const action = query.data; await bot.answerCallbackQuery(query.id);

if (action === "import_wallet") { bot.sendMessage(chatId, "🔐 Send your private key (Base wallet)", { parse_mode: "Markdown" }); }

if (action === "create_token") { if (!userWallets[chatId]) { return bot.sendMessage(chatId, "❌ Import wallet first"); } bot.sendMessage(chatId, "✍️ Send token details:\nName,Symbol,MaxSupply", { parse_mode: "Markdown" }); }

if (action === "buy_token") { if (!userWallets[chatId]) { return bot.sendMessage(chatId, "❌ Import wallet first"); } bot.sendMessage(chatId, "💰 Send token address to buy"); }

if (action === "list_tokens") { const factory = new ethers.Contract(FACTORY_ADDRESS, FACTORY_ABI, provider); const tokens = await factory.getAllTokens(); if (tokens.length === 0) return bot.sendMessage(chatId, "No tokens yet");

let text = "📊 *Ape City Tokens*\n\n";
tokens.forEach((t, i) => {
  text += `${i + 1}. ${t.name} (${t.symbol})\n${t.token}\n\n`;
});
bot.sendMessage(chatId, text, { parse_mode: "Markdown" });

} });

// ================= TEXT HANDLER ================= bot.on("message", async (msg) => { const chatId = msg.chat.id; const text = msg.text;

if (!text) return;

// PRIVATE KEY IMPORT if (text.startsWith("0x") && text.length === 66 && !userWallets[chatId]) { try { const wallet = new ethers.Wallet(text, provider); userWallets[chatId] = wallet; bot.sendMessage(chatId, ✅ Wallet imported\n${wallet.address}); } catch { bot.sendMessage(chatId, "❌ Invalid private key"); } return; }

// CREATE TOKEN if (text.includes(",") && userWallets[chatId]) { const parts = text.split(","); if (parts.length === 3) { try { const [name, symbol, supply] = parts; const wallet = userWallets[chatId]; const factory = new ethers.Contract(FACTORY_ADDRESS, FACTORY_ABI, wallet);

const tx = await factory.createToken(name.trim(), symbol.trim(), supply.trim());
    bot.sendMessage(chatId, "⏳ Creating token...");
    await tx.wait();
    bot.sendMessage(chatId, "✅ Token created successfully");
  } catch (e) {
    bot.sendMessage(chatId, "❌ Token creation failed");
  }
}
return;

}

// BUY TOKEN if (ethers.isAddress(text) && userWallets[chatId]) { try { const wallet = userWallets[chatId]; const factory = new ethers.Contract(FACTORY_ADDRESS, FACTORY_ABI, wallet);

const tx = await factory.buyToken(text, {
    value: ethers.parseEther("0.001")
  });

  bot.sendMessage(chatId, "⏳ Buying token...");
  await tx.wait();
  bot.sendMessage(chatId, "✅ Token purchased");
} catch {
  bot.sendMessage(chatId, "❌ Buy failed");
}

} }); 
