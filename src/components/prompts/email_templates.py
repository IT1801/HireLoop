def get_invite_email(name: str, role: str, slot: str) -> str:
    return f"""Subject: Interview Invitation - {role} at HireLoop
    
Hi {name},

Congratulations! We were very impressed with your application for the {role} position.
We would like to invite you for an interview. We have tentatively scheduled your slot for:
{slot}

Please let us know if this time works for you.

Best,
The HireLoop Team
"""

def get_accept_email(name: str, role: str) -> str:
    return f"""Subject: Offer to Join - {role} at HireLoop
    
Hi {name},

We are thrilled to offer you the position of {role} at HireLoop!
Your interview was excellent, and the team is very excited to have you on board.
We will be sending over the official offer letter shortly.

Welcome to the team!

Best,
The HireLoop Team
"""

def get_reject_email(name: str, role: str) -> str:
    return f"""Subject: Update on your application for {role}
    
Hi {name},

Thank you for taking the time to interview with us for the {role} position.
While we were impressed with your background, we have decided to move forward with another candidate who more closely matches our current needs.

We wish you all the best in your job search and future endeavors.

Best,
The HireLoop Team
"""
