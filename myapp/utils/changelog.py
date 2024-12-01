def get_changelog():
    """
    Returns a list of changelog entries in reverse chronological order
    """
    return [
        {
            'version': '1.3.1',
            'date': '2024-12-01',
            'changes': [
                'Added dedicated narrator role',
                'Updated role validation to account for narrator',
                'Modified role assignment logic to include narrator'
            ]
        },
        {
            'version': '1.3.0',
            'date': '2024-11-30',
            'changes': [
                'Added password reset functionality',
                'Added email verification functionality',
                'Added better error handling for login, register, and join room',
                'Added better error handling for password reset',
                'Added better error handling for email verification',
                'Added faster response times',
                'Added better styling for password reset and email verification',
            ]
        },
        {
            'version': '1.2.0',
            'date': '2024-11-28',
            'changes': [
                'Added Cloudflare Turnstile for captcha for login, register, and join room',
            ]
        },
        {
            'version': '1.1.1',
            'date': '2024-11-28',
            'changes': [
                'Moved changelog and report bug to the bottom of the page',
                'Fixed bug in role assignment',
                'Improved waiting room stability',
                'Added hyperlink to admin page (only visible to admins)',
            ]
        },
        {
            'version': '1.1.0',
            'date': '2024-03-20',
            'changes': [
                'Added changelog feature',
                'Improved mobile responsiveness',
                'Enhanced role display interface',
                'Added better error handling for database operations'
            ]
        },
        {
            'version': '1.0.1',
            'date': '2024-02-15',
            'changes': [
                'Fixed bug in role assignment',
                'Improved waiting room stability',
                'Added kick and ban functionality',
                'Enhanced session management'
            ]
        },
        {
            'version': '1.0.0',
            'date': '2024-01-28',
            'changes': [
                'Initial release',
                'Basic game functionality',
                'Role assignment system',
                'Player management',
                'Room creation and joining',
                'Basic authentication system'
            ]
        }
    ] 