import subprocess
import time

def send_sms_via_adb(phone_number, message):
    """
    Attempts to send an SMS using ADB by launching the default messaging app.
    Requires manual tap "Send" on the phone.
    """
    message_escaped = message.replace('"', '\\"').replace("'", "\\'").replace("`", "\\`").replace("$", "\\$")

    # Check if phone_number is a list (for potential future group SMS, though not fully implemented here)
    # For now, we expect a single string. If multiple numbers are given to this function directly,
    # they should be comma-separated for the sms: URI, e.g., "sms:num1,num2"
    # However, the main script will loop and call this function for each number individually for clarity.
    uri_data = f'sms:{phone_number}'

    cmd = [
        'adb', 'shell',
        'am', 'start',
        '-a', 'android.intent.action.SENDTO',
        '-d', uri_data,
        '--es', 'sms_body', '"{}"'.format(message_escaped),
        '--ez', 'exit_on_sent', 'true'
    ]

    print(f"\nExecuting command: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=15)

        if process.returncode == 0:
            print(f"SMS intent sent for {phone_number}. Check your phone to confirm sending.")
            print("The app might close automatically after you tap send, or you might need to close it.")
        else:
            print(f"Error sending SMS intent for {phone_number}:")
            if stdout:
                print(f"STDOUT: {stdout.decode().strip()}")
            if stderr:
                print(f"STDERR: {stderr.decode().strip()}")
        return process.returncode == 0

    except subprocess.TimeoutExpired:
        print("ADB command timed out for {phone_number}. The intent might have launched, but confirmation wasn't received.")
        if 'process' in locals() and process:
            process.kill()
        return False
    except FileNotFoundError:
        print("Error: ADB command not found. Is it installed and in your PATH?")
        return False
    except Exception as e:
        print(f"An unexpected error occurred for {phone_number}: {e}")
        return False

def check_adb_device():
    """Checks for connected and authorized ADB devices."""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True, timeout=10)
        device_lines = result.stdout.strip().split('\n')
        connected_devices = [line for line in device_lines[1:] if line.strip() and "\tdevice" in line]

        if not connected_devices:
            print("\nNo authorized Android device found or device is offline. Please check:")
            print("1. Phone is connected via USB.")
            print("2. USB Debugging is enabled in Developer Options.")
            print("3. You have authorized the computer for debugging on your phone.")
            print("\nADB 'devices' output:")
            print(result.stdout)
            return False
        else:
            print("\nConnected devices:")
            for device in connected_devices:
                print(f"- {device.split()[0]}")
            print("Proceeding...")
            return True

    except FileNotFoundError:
        print("ADB command not found. Please install Android SDK Platform Tools and add to PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error checking ADB devices: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("ADB 'devices' command timed out. Ensure ADB is working correctly.")
        return False

if __name__ == "__main__":
    print("--- ADB SMS Sender ---")

    if not check_adb_device():
        exit()

    # Get recipient numbers
    while True:
        recipient_input = input("\nEnter recipient phone number(s) (comma-separated for multiple, e.g., +123, +456): ").strip()
        if not recipient_input:
            print("Recipient number(s) cannot be empty. Please try again.")
            continue

        # Split by comma and strip whitespace from each number
        recipient_numbers = [num.strip() for num in recipient_input.split(',') if num.strip()]

        if not recipient_numbers:
            print("No valid phone numbers entered. Please try again.")
        else:
            break

    # Get message content
    while True:
        message_text = input("Enter the message content: ").strip()
        if message_text:
            break
        else:
            print("Message content cannot be empty. Please try again.")

    print("\n--- Summary ---")
    print(f"Recipient(s): {', '.join(recipient_numbers)}")
    print(f"Message: {message_text}")

    confirm = input("Do you want to proceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled by user.")
        exit()

    successful_sends = 0
    failed_sends = 0

    for i, number in enumerate(recipient_numbers):
        print(f"\n--- Sending to recipient {i+1} of {len(recipient_numbers)}: {number} ---")
        if send_sms_via_adb(number, message_text):
            successful_sends += 1
            print(f"SMS preparation for {number} initiated.")
        else:
            failed_sends += 1
            print(f"SMS preparation for {number} failed.")

        if i < len(recipient_numbers) - 1: # If not the last recipient
            try:
                # Wait for a few seconds to allow user to interact with the phone
                # and for the messaging app to potentially close.
                delay_seconds = 7
                print(f"Waiting {delay_seconds} seconds before proceeding to the next recipient...")
                print("Press Ctrl+C to skip waiting or stop.")
                time.sleep(delay_seconds)
            except KeyboardInterrupt:
                print("\nSkipping wait. Proceeding to next recipient or finishing.")
                # Optionally, ask if user wants to continue with next recipients or stop all
                stop_all = input("Do you want to stop sending to remaining recipients? (y/n): ").strip().lower()
                if stop_all == 'y':
                    print("Stopping further message sends.")
                    break # Exit the loop
    
    print("\n--- Sending Complete ---")
    print(f"Successfully initiated SMS prep for: {successful_sends} recipient(s).")
    print(f"Failed to initiate SMS prep for: {failed_sends} recipient(s).")

    # Note on Group SMS:
    # Some Android SMS apps might support sending to multiple recipients in one go
    # if you format the 'sms:' URI like 'sms:number1,number2,number3'.
    # This would open a group chat composer.
    # To try this (experimental, app-dependent):
    # 1. Modify the script to take all numbers as one string: `all_numbers_str = ",".join(recipient_numbers)`
    # 2. Call `send_sms_via_adb(all_numbers_str, message_text)` only ONCE.
    # This script uses individual sends for more predictable behavior across different SMS apps.