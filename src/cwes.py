from enum import Enum


class CWE(Enum):
    """
    CWE nums and official MITRE descriptions.
    """

    XSS = {
        "num": 79,
        "desc": "The product does not neutralize or incorrectly neutralizes user-controllable input before it is placed in output that is used as a web page that is served to other users.",
    }
    PATH_TRAVERSAL = {
        "num": 22,
        "desc": "The product uses external input to construct a pathname that is intended to identify a file or directory that is located underneath a restricted parent directory, but the product does not properly neutralize special elements within the pathname that can cause the pathname to resolve to a location that is outside of the restricted directory.",
    }
    CODE_INJECTION = {
        "num": 94,
        "desc": "The product constructs all or part of a code segment using externally-influenced input from an upstream component, but it does not neutralize or incorrectly neutralizes special elements that could modify the syntax or behavior of the intended code segment.",
    }
    SQL_INJECTION = {
        "num": 89,
        "desc": "The product constructs all or part of an SQL command using externally-influenced input from an upstream component, but it does not neutralize or incorrectly neutralizes special elements that could modify the intended SQL command when it is sent to a downstream component. Without sufficient removal or quoting of SQL syntax in user-controllable inputs, the generated SQL query can cause those inputs to be interpreted as SQL instead of ordinary user data.",
    }
    IMPROPER_ACCESS_CONTROL = {
        "num": 284,
        "desc": "The product does not restrict or incorrectly restricts access to a resource from an unauthorized actor.",
    }
    IMPROPER_AUTHENTICATION = {
        "num": 287,
        "desc": "When an actor claims to have a given identity, the product does not prove or insufficiently proves that the claim is correct.",
    }
    IMPROPER_OUTPUT_NEUTRALIZATION_FOR_LOGS = {
        "num": 117,
        "desc": "The product does not neutralize or incorrectly neutralizes output that is written to logs.",
    }
    OS_INJECTION = {
        "num": 78,
        "desc": "The product constructs all or part of an OS command using externally-influenced input from an upstream component, but it does not neutralize or incorrectly neutralizes special elements that could modify the intended OS command when it is sent to a downstream component.",
    }
    UNCONTROLLED_RESOURCE_CONSUMPTION = {
        "num": 400,
        "desc": "The product does not properly control the allocation and maintenance of a limited resource, thereby enabling an actor to influence the amount of resources consumed, eventually leading to the exhaustion of available resources.",
    }
    UNRESTRICTED_UPLOAD_WITH_DANGEROUS_FILE = {
        "num": 434,
        "desc": "The product allows the upload or transfer of dangerous file types that are automatically processed within its environment.",
    }
    INSUFFICIENTLY_PROTECTED_CREDENTIALS = {
        "num": 522,
        "desc": "The product transmits or stores authentication credentials, but it uses an insecure method that is susceptible to unauthorized interception and/or retrieval.",
    }
    INCORRECT_AUTHORIZATION = {
        "num": 863,
        "desc": "The product performs an authorization check when an actor attempts to access a resource or perform an action, but it does not correctly perform the check.",
    }
    IMPROPER_CHECK_OR_HANDLING_OF_EXCEPTIONAL_CONDITIONS = {
        "num": 703,
        "desc": "The product does not properly anticipate or handle exceptional conditions that rarely occur during normal operation of the product.",
    }
    IMPROPER_INPUT_VALIDATION = {
        "num": 20,
        "desc": "The product receives input or data, but it does not validate or incorrectly validates that the input has the properties that are required to process the data safely and correctly.",
    }
    OBSERVABLE_RESPONSE_DISCREPANCY = {
        "num": 204,
        "desc": "The product provides different responses to incoming requests in a way that reveals internal state information to an unauthorized actor outside of the intended control sphere.",
    }
    AUTHENTICATION_BYPASS_BY_CAPTURE_REPLAY = {
        "num": 294,
        "desc": "A capture-replay flaw exists when the design of the product makes it possible for a malicious user to sniff network traffic and bypass authentication by replaying it to the server in question to the same effect as the original message (or with minor changes).",
    }
    INSUFFICIENT_VERIFICATION_OF_DATA_AUTHENTICITY = {
        "num": 345,
        "desc": "The product does not sufficiently verify the origin or authenticity of data, in a way that causes it to accept invalid data.",
    }
    CROSS_SITE_REQUEST_FORGERY = {
        "num": 352,
        "desc": "The web application does not, or can not, sufficiently verify whether a well-formed, valid, consistent request was intentionally provided by the user who submitted the request.",
    }
    CONCURRENT_EXECUTION_WITH_IMPROPER_SYNCHRONIZATION = {
        "num": 362,
        "desc": "The product contains a concurrent code sequence that requires temporary, exclusive access to a shared resource, but a timing window exists in which the shared resource can be modified by another code sequence operating concurrently.",
    }
    SESSION_FIXATION = {
        "num": 384,
        "desc": "Authenticating a user, or otherwise establishing a new user session, without invalidating any existing session identifier gives an attacker the opportunity to steal authenticated sessions.",
    }
    IMPROPER_HANDLING_OF_HIGHLY_COMPRESSED_DATA = {
        "num": 409,
        "desc": "The product does not handle or incorrectly handles a compressed input with a very high compression ratio that produces a large output.",
    }
    DESERIALIZATION_OF_UNTRUSTED_DATA = {
        "num": 502,
        "desc": "The product deserializes untrusted data without sufficiently ensuring that the resulting data will be valid.",
    }
    URL_REDIRECTION_TO_UNTRUSTED_SITE = {
        "num": 601,
        "desc": "The web application accepts a user-controlled input that specifies a link to an external site, and uses that link in a redirect.",
    }
    INSUFFICIENT_SESSION_EXPIRATION = {
        "num": 613,
        "desc": "According to WASC, \"Insufficient Session Expiration is when a web site permits an attacker to reuse old session credentials or session IDs for authorization.\"",
    }
    AUTHORIZATION_BYPASS_THROUGH_USER_CONTROLLED_KEY = {
        "num": 639,
        "desc": "The system's authorization functionality does not prevent one user from gaining access to another user's data or record by modifying the key value identifying the data.",
    }
    WEAK_PASSWORD_RECOVERY_MECHANISM_FORGOTTEN_PASSWORD = {
        "num": 640,
        "desc": "The product contains a mechanism for users to recover or change their passwords without knowing the original password, but the mechanism is weak.",
    }
    IMPROPERLY_CONTROLLED_MODIFICATION_OF_DYNAMICALLY_DETERMINED_OBJECT_ATTRIBUTES = {
        "num": 915,
        "desc": "The product receives input from an upstream component that specifies multiple attributes, properties, or fields that are to be initialized or updated in an object, but it does not properly control which attributes can be modified.",
    }
    SERVER_SIDE_REQUEST_FORGERY = {
        "num": 918,
        "desc": "The web server receives a URL or similar request from an upstream component and retrieves the contents of this URL, but it does not sufficiently ensure that the request is being sent to the expected destination.",
    }


def get_cwe_by_id(cwe_id):
    for cwe in CWE:
        if cwe.value["num"] == cwe_id:
            return cwe
    raise NotImplementedError(f"CWE-{cwe_id} is not implemented")
