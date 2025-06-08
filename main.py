#!/usr/bin/env python3

import subprocess
import time
import argparse
import sys
from typing import List, Optional

# --- UI Enhancements: ANSI Colors ---
class Colors:
    """A class to hold ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_color(color: str, message: str):
    """Prints a message in the specified color."""
    print(f"{color}{message}{Colors.ENDC}")

# --- Core Logic ---
class AdbSmsHelper:
    """A helper class to interact with an Android device via ADB for sending SMS intents."""

    def __init__(self, adb_path: str = 'adb'):
        self.adb_path = adb_path

    def check_device_connection(self) -> bool:
        """
        Checks for connected and authorized ADB devices.
        Returns True if at least one device is ready, False otherwise.
        """
        print_color(Colors.OKBLUE, "Checking for connected ADB devices...")
        try:
            result = subprocess.run(
                [self.adb_path, 'devices'],
                capture_output=True, text=True, check=True, timeout=10
            )
            device_lines = result.stdout.strip().split('\n')
            # Filter for lines that represent an active, authorized device
            connected_devices = [line for line in device_lines[1:] if line.strip() and "\tdevice" in line]

            if not connected_devices:
                print_color(Colors.FAIL, "\nError: No authorized Android device found.")
                print("Please ensure that:")
                print("1. Your phone is connected via USB.")
                print("2. 'USB Debugging' is enabled in Developer Options.")
                print("3. You have authorized this computer for debugging on your phone.")
                return False
            else:
                print_color(Colors.OKGREEN, "\nFound connected device(s):")
                for device in connected_devices:
                    print(f"- {device.split()[0]}")
                return True

        except FileNotFoundError:
            print_color(Colors.FAIL, f"Error: The command '{self.adb_path}' was not found.")
            print("Please install Android SDK Platform Tools and ensure 'adb' is in your system's PATH.")
            return False
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print_color(Colors.FAIL, f"An error occurred while checking for ADB devices: {e}")
            if hasattr(e, 'stderr'):
                print(f"ADB Error Output: {e.stderr}")
            return False

    def send_sms_intent(self, phone_number: str, message: str) -> bool:
        """
        Sends an intent to the Android device to open the default messaging app
        with the recipient and message pre-filled.

        Args:
            phone_number: The recipient's phone number.
            message: The message body.

        Returns:
            True if the ADB command was sent successfully, False otherwise.
        """
        print(f"\nAttempting to open SMS composer for {Colors.OKCYAN}{phone_number}{Colors.ENDC}...")
        
        # The 'am start' command to open the SMS app.
        # No extra quotes are needed around the message; subprocess handles arguments.
        command = [
            self.adb_path, 'shell', 'am', 'start',
            '-a', 'android.intent.action.SENDTO',
            '-d', f'sms:{phone_number}',
            '--es', 'sms_body', message,
            '--ez', 'exit_on_sent', 'true'
        ]

        try:
            # Using Popen to get more control and avoid blocking indefinitely if the shell hangs
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(timeout=15)

            if process.returncode == 0:
                print_color(Colors.OKGREEN, "Intent sent successfully! Please check your phone to tap 'Send'.")
                return True
            else:
                print_color(Colors.FAIL, f"Error sending intent for {phone_number}.")
                if stderr:
                    # Often, the error message from 'am' is on stderr.
                    print_color(Colors.FAIL, f"ADB Error: {stderr.strip()}")
                else:
                    print_color(Colors.WARNING, "ADB command failed with no specific error message.")
                return False

        except subprocess.TimeoutExpired:
            print_color(Colors.FAIL, f"ADB command timed out for {phone_number}.")
            return False
        except Exception as e:
            print_color(Colors.FAIL, f"An unexpected error occurred for {phone_number}: {e}")
            return False

def run_interactive_mode() -> tuple[List[str], str]:
    """Runs the script in interactive mode, prompting the user for input."""
    while True:
        recipient_input = input(f"Enter recipient phone number(s) (comma-separated): ").strip()
        if not recipient_input:
            print_color(Colors.WARNING, "Input cannot be empty. Please try again.")
            continue
        recipient_numbers = [num.strip() for num in recipient_input.split(',') if num.strip()]
        if recipient_numbers:
            break
        else:
            print_color(Colors.WARNING, "No valid phone numbers entered. Please try again.")

    while True:
        message_text = input("Enter the message content: ").strip()
        if message_text:
            break
        else:
            print_color(Colors.WARNING, "Message content cannot be empty.")
    
    return recipient_numbers, message_text

def main():
    """Main function to parse arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="A CLI tool to send SMS messages via an ADB-connected Android device.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  Interactive mode:
    python main.py

  Direct mode:
    python main.py -n "+15551234567" -m "Hello there!"
    python main.py -n "+15551234567,+15557654321" -m "Group message" -d 10
"""
    )
    parser.add_argument("-n", "--numbers", help="One or more recipient phone numbers, comma-separated.")
    parser.add_argument("-m", "--message", help="The content of the SMS message.")
    parser.add_argument("-d", "--delay", type=int, default=7, help="Delay in seconds between sending to multiple recipients (default: 7).")

    args = parser.parse_args()

    print_color(Colors.HEADER, "--- ADB SMS Sender ---")
    print("Prepares SMS messages on your phone. You must tap 'Send' manually on the device.\n")

    helper = AdbSmsHelper()
    if not helper.check_device_connection():
        sys.exit(1)

    if args.numbers and args.message:
        # Direct mode from arguments
        recipient_numbers = [num.strip() for num in args.numbers.split(',')]
        message_text = args.message
        print("\nUsing provided arguments:")
    else:
        # Interactive mode
        recipient_numbers, message_text = run_interactive_mode()
        print("\n--- Summary ---")
    
    print(f"{Colors.BOLD}Recipient(s):{Colors.ENDC} {', '.join(recipient_numbers)}")
    print(f"{Colors.BOLD}Message:{Colors.ENDC} \"{message_text}\"")
    
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print_color(Colors.WARNING, "Operation cancelled.")
        sys.exit(0)

    successful_sends = 0
    total_sends = len(recipient_numbers)

    for i, number in enumerate(recipient_numbers):
        if helper.send_sms_intent(number, message_text):
            successful_sends += 1
        
        if i < total_sends - 1:
            try:
                print_color(Colors.OKBLUE, f"\nWaiting {args.delay} seconds before next recipient. Press Ctrl+C to skip.")
                time.sleep(args.delay)
            except KeyboardInterrupt:
                print_color(Colors.WARNING, "\nWait skipped by user.")

    print_color(Colors.HEADER, "\n--- Task Complete ---")
    print_color(Colors.OKGREEN, f"Successfully initiated: {successful_sends} of {total_sends} messages.")
    if successful_sends < total_sends:
        print_color(Colors.FAIL, f"Failed to initiate: {total_sends - successful_sends} of {total_sends} messages.")

if __name__ == "__main__":
    main()