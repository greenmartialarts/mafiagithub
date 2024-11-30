def get_device_type(request):
    """
    Detect the type of device based on User-Agent
    Returns: 'mobile', 'tablet', or 'desktop'
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # Define patterns for different devices
    mobile_patterns = ['iphone', 'android', 'mobile', 'webos', 'ipod', 'blackberry']
    tablet_patterns = ['ipad', 'tablet']
    
    # Check for mobile devices
    if any(pattern in user_agent for pattern in mobile_patterns):
        return 'mobile'
    
    # Check for tablets
    if any(pattern in user_agent for pattern in tablet_patterns):
        return 'tablet'
    
    # Default to desktop
    return 'desktop' 