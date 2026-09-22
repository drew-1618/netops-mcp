import ipaddress
import re

# allows 1-63 chars per label, letters/numbers/hyphens (not starting/ending with hyphen), separated by dots
HOSTNAME_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$|"
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
)

def validate_target(target: str) -> tuple[bool, str]:
  """
  Validates that a ping target is a syntactically valid IPv4/IPv6 address or
  standard hostname. Blocks flags, spaces, and shell injection tokens.
  """

  if not target or not isinstance(target, str):
    return False, "Target must be a non-empty string"

  cleaned = target.strip()

  # reject obvious flagh injections or command chaining
  if cleaned.startswith("-") or any(char in cleaned for char in [";", "&", "|", "`", "$", " ", "\t", "\n"]):
    return (False, f"Target contains invalid of potentially malicious characters: {target}")

  # check if valid IP
  try:
    ipaddress.ip_address(cleaned)
    return True, ""
  except ValueError:
    pass

  # check if valid hostname
  if HOSTNAME_REGEX.match(cleaned):
    return True, ""

  return (False, f"Target '{target}' is neither a valid IP address nor a valid hostname")

def validate_count(count: int, min_val:int = 1, max_val: int = 10) -> tuple[bool, str]:
    """
    Validates that the ping count is an integer within the specified range.
    """
    if not isinstance(count, int):
        return False, "Count must be an integer"
    if count < min_val or count > max_val:
        return False, f"Count must be between {min_val} and {max_val}"
    return True, ""