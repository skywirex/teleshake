from datetime import datetime
from utils import (
    WALLET, HSD, check_wallet_existing, fetch_and_save_names, renew_names,
    get_wallet_and_node_info, find_soonest_expiring_name
)
from bot_telegram import send_telegram_message

def main():
    """Run a single cycle – designed to be called by cron every hour"""
    try:
        wallet, hsd = WALLET(), HSD()
        check_wallet_existing(wallet)    # Will fail fast if wallet is missing

        fetch_and_save_names(wallet)
        renewed_names = renew_names(wallet)
        info = get_wallet_and_node_info(wallet, hsd)
        soonest_expiring = find_soonest_expiring_name()

        # === Build the message ===
        message_lines = [ f"<b>Teleshake Update ({datetime.now ().strftime ( '%Y-%m-%d %H:%M:%S' )})</b>",
                          "\n<b>INFO:</b>",
                          f"Account: <code>{info [ 'account' ]}</code> | Height: <code>{info [ 'block_height' ]}</code>",
                          f"Balance: <code>{info [ 'balance' ]} HNS</code>",
                          f"Address: <code>{info [ 'full_receiving_address' ]}</code>",
                          "\n<b>SOONEST EXPIRING NAME:</b>" ]

        if soonest_expiring["name"]:
            message_lines.append(f"Name: <code>{soonest_expiring['name']}</code>")
            message_lines.append(f"Expires: <code>{soonest_expiring['expiration_date']}</code>")
            message_lines.append(f"Days until expiration: <code>{soonest_expiring['days_until_expire']}</code>")
        else:
            message_lines.append("No names found")

        message_lines.append("\n<b>RENEWAL:</b>")
        if renewed_names:
            message_lines.append("Renewed the following names:")
            message_lines.extend([f"- <code>{name}</code>" for name in renewed_names])
        else:
            message_lines.append("No names required renewal")

        message = "\n".join(message_lines)
        send_telegram_message(message, parse_mode="HTML")
        print(f"{datetime.now()} - Cycle completed successfully.")

    except Exception as e:
        error_message = f"<b>Teleshake ERROR ({datetime.now().strftime('%Y-%m-%d %H:%M')}):</b>\n{str(e)}"
        print(f"Error: {e}")
        try:
            send_telegram_message(error_message, parse_mode="HTML")
        except:
            pass  # Don't crash if Telegram fails too


if __name__ == "__main__":
    main()