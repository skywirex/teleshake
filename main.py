import time
from datetime import datetime
from utils import (
    WALLET, HSD, check_wallet_existing, fetch_and_save_names, renew_names,
    get_wallet_and_node_info, find_soonest_expiring_name, LOOP_PERIOD_SECONDS
)
from bot_telegram import send_telegram_message

def main():
    """Main function to manage wallet names and renewals with periodic execution."""
    while True:  # Outer loop for critical restarts
        try:
            wallet, hsd = WALLET(), HSD()
            check_wallet_existing(wallet)    # Run once at startup – fails if wallet missing

            while True:  # Inner loop for regular execution
                try:
                    fetch_and_save_names(wallet)
                    renewed_names = renew_names(wallet)
                    info = get_wallet_and_node_info(wallet, hsd)
                    soonest_expiring = find_soonest_expiring_name()

                    # Construct formatted message with HTML
                    message_lines = [
                        f"<b>Teleshake Update ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})</b>"
                    ]
                    # Wallet and node info
                    message_lines.append("\n<b>INFO:</b>")
                    message_lines.append(f"Account: <code>{info['account']}</code> | Height: <code>{info['block_height']}</code>")
                    message_lines.append(f"Balance: <code>{info['balance']} HNS</code>")
                    message_lines.append(f"Address: <code>{info['full_receiving_address']}</code>")

                    # Soonest expiring name
                    message_lines.append("\n<b>SOONEST EXPIRING NAME:</b>")
                    if soonest_expiring["name"]:
                        message_lines.append(f"Name: <code>{soonest_expiring['name']}</code>")
                        message_lines.append(f"Expires: <code>{soonest_expiring['expiration_date']}</code>")
                        message_lines.append(f"Days until expiration: <code>{soonest_expiring['days_until_expire']}</code>")
                    else:
                        message_lines.append("No names found")

                    # Renewal results
                    message_lines.append("\n<b>RENEWAL:</b>")
                    if renewed_names:
                        message_lines.append("Renewed the following names:")
                        message_lines.extend([f"- <code>{name}</code>" for name in renewed_names])
                    else:
                        message_lines.append("No names required renewal")

                    message = "\n".join(message_lines)
                    send_telegram_message(message, parse_mode="HTML")
                    print(f"Notification sent. Sleeping for {LOOP_PERIOD_SECONDS} seconds...")

                except Exception as e:
                    error_message = f"<b>Error in Teleshake:</b> {str(e)}"
                    print(f"Inner loop error: {str(e)}")
                    send_telegram_message(error_message, parse_mode="HTML")

                time.sleep(LOOP_PERIOD_SECONDS)

        except Exception as outer_e:
            error_message = f"<b>Critical Error in Teleshake, restarting in {LOOP_PERIOD_SECONDS}s:</b> {str(outer_e)}"
            print(f"Critical error: {str(outer_e)}")
            try:
                send_telegram_message(error_message, parse_mode="HTML")
            except Exception as telegram_error:
                print(f"Failed to send Telegram error message: {telegram_error}")
            time.sleep(LOOP_PERIOD_SECONDS)

if __name__ == "__main__":
    main()