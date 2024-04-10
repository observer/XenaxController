import socket
import time

class XenaxController:
    # Initialize the XenaxController class with default parameters for the magnetic rail control
    def __init__(self, ip_address, port=10001, limit_left=0, limit_right=None, speed=100000, acceleration=1000000):
        # Network settings for connecting to the controller
        self.ip_address = ip_address
        self.port = port
        # Position limits for the controller's movement
        self.limit_left = limit_left
        self.limit_right = limit_right
        # Movement parameters
        self.set_speed(speed, during_init=True)
        self.set_acceleration(acceleration, during_init=True)
        # Networking
        self.socket = None
        self.last_response = ""  # Cache for the last response for quick access

    @property
    def center_position(self):
        # Calculate and return the center position between left and right limits
        return (self.limit_left + self.limit_right) // 2

    @property
    def min_position(self):
        # Alias for limit_left, for ease of understanding
        return self.limit_left

    @property
    def max_position(self):
        # Alias for limit_right, for ease of understanding
        return self.limit_right

    # Setter for min_position updates limit_left
    @min_position.setter
    def min_position(self, value):
        self.limit_left = value

    # Setter for max_position updates limit_right
    @max_position.setter
    def max_position(self, value):
        self.limit_right = value

    def connect(self):
        # Establishes a TCP connection to the controller
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip_address, self.port))
        self.initialize()  # Initialize the controller settings after connecting

    def initialize(self):
        # Sends a series of commands to the controller to initialize it
        commands = ["ECH0", "PW", "EVT1", "HORM", "EVT0"]
        for cmd in commands:
            self.send_command(cmd)
            time.sleep(0.2)  # Pause between commands to ensure they are processed
        # Re-apply speed and acceleration settings after initialization
        self.set_speed(self.speed)
        self.set_acceleration(self.acceleration)

    def disconnect(self):
        # Sends a power-off command and closes the TCP connection
        self.send_command("PQ")
        self.socket.close()

    def send_command(self, command):
        # Sends a command to the controller and stores the response
        original_blocking_mode = self.socket.getblocking()  # Save current blocking state
        self.socket.setblocking(1)  # Set socket to blocking mode
        self.clear_buffer()  # Clear buffer to ensure fresh command execution
        full_command = command + '\r'  # Append carriage return to command
        self.socket.sendall(full_command.encode())  # Send the command
        self.last_response = self.read_response()  # Read and store the response
        self.socket.setblocking(original_blocking_mode)  # Restore original blocking state

    def clear_buffer(self):
        # Clears any residual data from the socket to avoid stale data interference
        self.socket.settimeout(0.1)  # Short timeout for non-blocking read
        try:
            while True:
                data = self.socket.recv(1024)
                if not data:
                    break  # Exit loop if no more data
        except socket.timeout:
            pass  # Expected when buffer is cleared
        finally:
            self.socket.settimeout(None)  # Reset to default blocking mode

    def read_response(self):
        # Reads, decodes, and cleans up the response from the controller
        try:
            response_bytes = self.socket.recv(1024)
            response_str = response_bytes.decode().strip('> \r\n')  # Clean response string
            return response_str
        except socket.error as e:
            print(f"Socket error: {e}")
            return ""

    def response(self):
        # Returns the last received and cleaned response
        return self.last_response

    def set_speed(self, value, during_init=False):
        # Sets the movement speed of the controller, with validation
        if 50 <= value <= 10000000:
            self.speed = value
            if not during_init:
                self.send_command(f"SP{value}")
        else:
            raise ValueError("Speed value out of range")

    def get_speed(self):
        # Returns the currently set speed
        return self.speed

    def set_acceleration(self, value, during_init=False):
        # Sets the acceleration parameter of the controller, with validation
        if 100000 <= value <= 10000000:
            self.acceleration = value
            if not during_init:
                self.send_command(f"AC{value}")
        else:
            raise ValueError("Acceleration value out of range")

    def get_acceleration(self):
        # Returns the currently set acceleration
        return self.acceleration

    def set_position(self, value):
        # Commands the controller to move to a specific position, with validation
        if isinstance(value, float):  # Convert floats to int for precision
            value = int(value)
        elif not isinstance(value, int):
            raise TypeError("Position value must be an integer")
    
        if self.limit_left <= value <= self.limit_right:
            self.send_command(f"G{value}")
        else:
            raise ValueError("Position out of limits")

    def get_position(self):
        # Requests and returns the current position from the controller
        self.send_command("TP")
        return self.response()  # Directly use cleaned response

    def jog_positive(self):
        # Command to move the controller positively along the rail
        self.send_command("JP")

    def jog_negative(self):
        # Command to move the controller negatively along the rail
        self.send_command("JN")

    def power_on(self):
        # Power on the controller
        self.send_command("PW")

    def power_off(self):
        # Power off the controller
        self.send_command("PQ")

