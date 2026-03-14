from user_agents import parse


def get_device_info(request):
    # Get the User-Agent string from the request headers
    user_agent_string = request.META.get("HTTP_USER_AGENT", "")

    # Parse the User-Agent string
    user_agent = parse(user_agent_string)

    # Get the operating system and browser name
    operating_system = f"{user_agent.os.family} {user_agent.os.version_string}"
    browser_name = f"{user_agent.browser.family} {user_agent.browser.version_string}"

    return operating_system, browser_name
