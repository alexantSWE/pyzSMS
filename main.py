import subprocess
import time

def send_sms_via_adb(phone_number, message):
    """
    Attempts to send an SMS using ADB by launching the default messaging app.
    Note: This will likely require you to manually tap "Send" on the phone.
    """
    message_escaped = message.replace('"', '\\"').replace("'", "\\'").replace("`", "\\`").replace("$", "\\$")

    cmd = [
        'adb', 'shell',
        'am', 'start',
        '-a', 'android.intent.action.SENDTO',
        '-d', 'sms:{}'.format(phone_number),
        '--es', 'sms_body', '"{}"'.format(message_escaped),
        '--ez', 'exit_on_sent', 'true'
    ]

    print(f"\nExecuting command: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=15)

        if process.returncode == 0:
            print(f"SMS intent sent to {phone_number}. Check your phone to confirm sending.")
            print("The app might close automatically after you tap send, or you might need to close it.")
        else:
            print(f"Error sending SMS intent to {phone_number}:")
            if stdout:
                print(f"STDOUT: {stdout.decode().strip()}")
            if stderr:
                print(f"STDERR: {stderr.decode().strip()}")
        return process.returncode == 0

    except subprocess.TimeoutExpired:
        print("ADB command timed out. The intent might have launched, but confirmation wasn't received.")
        if 'process' in locals() and process: # Check if process was initialized
            process.kill()
        return False
    except FileNotFoundError:
        print("Error: ADB command not found. Is it installed and in your PATH?")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    print("--- ADB SMS Sender ---")

    # 1. Check for connected devices
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True, timeout=10)
        # Check if any device is listed and not unauthorized/offline
        device_lines = result.stdout.strip().split('\n')
        connected_devices = [line for line in device_lines[1:] if line.strip() and "\tdevice" in line]

        if not connected_devices:
            print("\nNo authorized Android device found or device is offline. Please check:")
            print("1. Phone is connected via USB.")
            print("2. USB Debugging is enabled in Developer Options.")
            print("3. You have authorized the computer for debugging on your phone.")
            print("\nADB 'devices' output:")
            print(result.stdout)
            exit()
        else:
            print("\nConnected devices:")
            for device in connected_devices:
                print(f"- {device.split()[0]}") # Print device ID
            print("Proceeding...")

    except FileNotFoundError:
        print("ADB command not found. Please install Android SDK Platform Tools and add to PATH.")
        exit()
    except subprocess.CalledProcessError as e:
        print(f"Error checking ADB devices: {e.stderr}")
        exit()
    except subprocess.TimeoutExpired:
        print("ADB 'devices' command timed out. Ensure ADB is working correctly.")
        exit()

    # 2. Get user input for phone number
    while True:
        recipient_number = input("\nEnter recipient's phone number (e.g., +12345678900): ").strip()
        if recipient_number: # Basic check if input is not empty
            break
        else:
            print("Phone number cannot be empty. Please try again.")

    # 3. Get user input for message content
    while True:
        message_text = input("Enter the message content: ").strip()
        if message_text: # Basic check if input is not empty
            break
        else:
            print("Message content cannot be empty. Please try again.")

    print(f"\nPreparing to send to: {recipient_number}")
    print(f"Message: {message_text}")

    confirm = input("Do you want to proceed? (y/n): ").strip().lower()
    if confirm == 'y':
        if send_sms_via_adb(recipient_number, message_text):
            print("\nSMS preparation initiated successfully.")
        else:
            print("\nSMS preparation failed.")
    else:
        print("Operation cancelled by user.")