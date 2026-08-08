import logging
logger = logging.getLogger("soc-response")

def execute_response(action, source_ip):
    # Safe portfolio implementation: simulate infrastructure changes.
    if action == "block_ip":
        logger.warning("SIMULATED RESPONSE: block IP %s", source_ip)
        return f"SIMULATED: blocked IP {source_ip}"
    if action == "disable_account":
        logger.warning("SIMULATED RESPONSE: disable account for %s", source_ip)
        return f"SIMULATED: disabled account associated with {source_ip}"
    return "No response action executed"
