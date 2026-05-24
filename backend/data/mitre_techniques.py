"""Curated MITRE ATT&CK technique dictionary for the AI SOC Assistant.

This is the in-app lookup an analyst gets when the LLM cites a technique
(`T1190`, `T1078`, ...) in a triage answer. We do not embed all 700+ ATT&CK
techniques - only the ~30 the LLM most commonly emits for SOC triage. For
anything not in this dictionary the UI falls back to a link to
https://attack.mitre.org/techniques/Txxxx/ which is the authoritative source.

Each entry: id, name, tactic, description, detection_indicators, mitigations,
mitre_url. Tactics use the MITRE Enterprise matrix names verbatim so they
match what appears in attack.mitre.org tactic columns.
"""

_BASE = "https://attack.mitre.org/techniques/{tid}/"


def _entry(
    tid: str,
    name: str,
    tactic: str,
    description: str,
    indicators: list[str],
    mitigations: list[str],
) -> dict:
    return {
        "id": tid,
        "name": name,
        "tactic": tactic,
        "description": description.strip(),
        "detection_indicators": indicators,
        "mitigations": mitigations,
        "mitre_url": _BASE.format(tid=tid.replace(".", "/")),
    }


MITRE_TECHNIQUES: dict[str, dict] = {entry["id"]: entry for entry in [
    # ── Initial Access ───────────────────────────────────────────────────────
    _entry(
        "T1078", "Valid Accounts", "Initial Access / Persistence / Privilege Escalation / Defense Evasion",
        """Adversaries obtain and abuse credentials of existing accounts (local,
        domain, default, or cloud) to bypass access controls. This is one of
        the most common ATT&CK techniques because it blends with normal
        traffic.""",
        [
            "Login from an unfamiliar geography or device for a known user",
            "Successful login immediately after a burst of failed attempts (T1110)",
            "Use of dormant or service accounts during off-hours",
            "Privileged login from a non-jump-host",
        ],
        [
            "Enforce MFA on every account, especially privileged and remote-access",
            "Apply conditional-access / risk-based policies at the IdP",
            "Disable or rotate default and service-account credentials",
            "Continuously baseline behaviour (UEBA) and alert on deviation",
        ],
    ),
    _entry(
        "T1110", "Brute Force", "Credential Access",
        """Adversaries try many passwords (or many usernames) to discover valid
        credentials. Includes password guessing, password spraying, credential
        stuffing, and password cracking against captured hashes.""",
        [
            "High rate of authentication failures on one or many accounts",
            "Lockouts spreading across many accounts (spraying)",
            "Failed logins followed by a success from the same IP",
            "Authentication attempts that cycle through common passwords",
        ],
        [
            "Account-lockout thresholds and exponential backoff",
            "MFA so a guessed password is not sufficient",
            "Threat-intel feeds for known credential-dump IPs",
            "Anomaly detection on login velocity",
        ],
    ),
    _entry(
        "T1190", "Exploit Public-Facing Application", "Initial Access",
        """Adversaries exploit a weakness in an internet-facing application
        (web server, VPN gateway, RDP service, etc.) to gain initial access.
        Often the first step in a multi-stage intrusion.""",
        [
            "Anomalous request patterns to admin URLs",
            "Web-shell artefacts on the host",
            "Exploitation signatures from IDS / WAF",
            "Unusual outbound connections from the web server right after a request burst",
        ],
        [
            "Keep public-facing software patched (especially CVE-listed)",
            "Run a WAF in blocking mode and review its alerts",
            "Network-segment the DMZ - no admin path to the internal network",
            "Minimise externally exposed services (zero-trust principle)",
        ],
    ),
    _entry(
        "T1133", "External Remote Services", "Initial Access / Persistence",
        """Adversaries use legitimate remote-access services (VPN, RDP, SSH,
        Citrix) to access or persist inside a network, typically with valid
        accounts (T1078).""",
        [
            "RDP / SSH / VPN login from an unusual location",
            "Concurrent sessions for one user from different geos",
            "Long-lived sessions outside business hours",
        ],
        [
            "Force MFA on every remote-access path",
            "Limit who can reach RDP / SSH at the network layer (jump hosts)",
            "Disable services that don't need to be exposed",
        ],
    ),
    _entry(
        "T1566", "Phishing", "Initial Access",
        """Adversaries send messages (email, SMS, chat) that lure users into
        executing malicious payloads or handing over credentials. Sub-techniques
        cover Spearphishing Attachment, Link, and via Service.""",
        [
            "User-reported suspicious email",
            "Email gateway flagged but-not-blocked verdicts",
            "Outbound connection to a credential-harvesting domain shortly after an email open",
        ],
        [
            "User awareness training plus a one-click report-phish button",
            "DMARC / SPF / DKIM at the email gateway",
            "Sandbox attachments and rewrite URLs",
        ],
    ),

    # ── Execution ────────────────────────────────────────────────────────────
    _entry(
        "T1059", "Command and Scripting Interpreter", "Execution",
        """Adversaries abuse command shells and scripting languages
        (PowerShell, cmd, bash, Python, JavaScript) to execute malicious code.
        Sub-techniques cover specific interpreters, e.g. T1059.001 PowerShell.""",
        [
            "Encoded-command PowerShell (`powershell -enc ...`)",
            "Unusual parent / child process chains (office app spawning powershell)",
            "Use of LOLBins (rundll32, wmic, mshta) launching scripts",
            "Script-block logging entries with obfuscated content",
        ],
        [
            "Enable PowerShell ScriptBlock logging and ship to SIEM",
            "Constrained Language Mode and AMSI on Windows",
            "AppLocker / WDAC to control which interpreters run",
        ],
    ),
    _entry(
        "T1204", "User Execution", "Execution",
        """Adversaries rely on a user to execute the payload - opening an
        attachment, clicking a link, running a downloaded file.""",
        [
            "Office macro execution from an email-borne attachment",
            "Run of a downloaded executable shortly after a click event",
        ],
        [
            "Block macros from internet-sourced documents",
            "Mark-of-the-web aware EDR rules",
            "User awareness on attachment / link risks",
        ],
    ),

    # ── Persistence ──────────────────────────────────────────────────────────
    _entry(
        "T1098", "Account Manipulation", "Persistence / Privilege Escalation",
        """Adversaries change permissions or attributes on existing accounts
        to maintain access - adding to privileged groups, modifying
        credentials, adding alternate authentication.""",
        [
            "Group-membership change to a privileged group",
            "Password change for an account that was not used recently",
            "Addition of an authentication method (key, certificate) to an admin account",
        ],
        [
            "Approval workflow for privileged-group changes",
            "Alerting on every change to admin / break-glass accounts",
            "Periodic access review and credential rotation",
        ],
    ),
    _entry(
        "T1136", "Create Account", "Persistence",
        """Adversaries create local, domain, or cloud accounts to keep access
        without using the original entry vector.""",
        [
            "New account created outside the change window",
            "Account created with admin or high-privileged group membership",
            "Account created by a non-IT user",
        ],
        [
            "Centralise account provisioning via an IdP",
            "Alert on every account creation in privileged scopes",
            "Disable local account creation where possible",
        ],
    ),
    _entry(
        "T1547", "Boot or Logon Autostart Execution", "Persistence / Privilege Escalation",
        """Adversaries configure system settings to automatically execute code
        at boot or login. Sub-techniques include registry Run keys, scheduled
        tasks, services, and startup folder.""",
        [
            "New entries in Windows registry Run keys",
            "Newly-created scheduled task with an unusual command line",
            "New service binary in user-writable paths",
        ],
        [
            "Application allow-listing",
            "EDR rules covering common autorun keys",
            "Audit Sysinternals Autoruns periodically",
        ],
    ),

    # ── Privilege Escalation ─────────────────────────────────────────────────
    _entry(
        "T1068", "Exploitation for Privilege Escalation", "Privilege Escalation",
        """Adversaries exploit a software vulnerability to elevate privileges
        on a host.""",
        [
            "Exploit-related crash in a privileged process",
            "Unusual access pattern to /etc/shadow, LSASS, or kernel objects",
            "Sudden privilege gain by an account that did not have it",
        ],
        [
            "Keep host OS and drivers patched",
            "Privileged-Access Workstations for admin work",
            "EDR rules covering known kernel-exploit primitives",
        ],
    ),
    _entry(
        "T1548", "Abuse Elevation Control Mechanism", "Privilege Escalation / Defense Evasion",
        """Adversaries abuse legitimate elevation paths (UAC bypass, sudo,
        setuid, IAM role assumption) to gain higher privileges without
        exploiting a vulnerability.""",
        [
            "UAC-bypass technique detection on Windows",
            "Unusual sudo invocations or `sudo -i` chains",
            "Unexpected `AssumeRole` calls in cloud audit logs",
        ],
        [
            "Set UAC to Always Notify",
            "Tightly scope sudoers / IAM policies",
            "Just-in-time elevation with approval",
        ],
    ),

    # ── Defense Evasion ──────────────────────────────────────────────────────
    _entry(
        "T1027", "Obfuscated Files or Information", "Defense Evasion",
        """Adversaries hide payloads using encoding, encryption, packing, or
        steganography to evade signature-based detection.""",
        [
            "Base64-encoded blobs in command lines",
            "Packed executables (high entropy, no readable strings)",
            "Scripts that decode-and-execute at runtime",
        ],
        [
            "AMSI on Windows to inspect post-decode content",
            "EDR rules on `-enc`, `IEX`, `FromBase64String`",
            "Block packers known to be used in malware",
        ],
    ),
    _entry(
        "T1070", "Indicator Removal", "Defense Evasion",
        """Adversaries delete or alter generated artefacts (logs, files,
        timestamps) to remove evidence of their activity.""",
        [
            "Event-log clear operations (Windows event 1102)",
            "Sudden gap in audit-log timestamps",
            "Timestomping - file mtime older than birth time",
        ],
        [
            "Ship logs off-host in near real time",
            "Append-only / immutable log storage",
            "Alert specifically on log-clear events",
        ],
    ),
    _entry(
        "T1112", "Modify Registry", "Defense Evasion",
        """Adversaries modify Windows registry keys to hide configuration,
        disable controls, or persist (overlaps with T1547).""",
        [
            "Registry modification to a security-tool autostart key",
            "Setting that disables Defender or LSASS protection",
        ],
        [
            "Tamper protection in Defender / EDR",
            "Audit registry changes to known sensitive keys",
        ],
    ),

    # ── Credential Access ────────────────────────────────────────────────────
    _entry(
        "T1003", "OS Credential Dumping", "Credential Access",
        """Adversaries dump credentials from the OS (LSASS memory, SAM, NTDS,
        cached creds). Often the pivot point between initial-access and
        lateral movement.""",
        [
            "Process accessing LSASS handle with PROCESS_VM_READ",
            "Tool signatures (Mimikatz, Pypykatz, lsassy)",
            "Copy of NTDS.dit from a domain controller",
        ],
        [
            "Credential Guard on Windows",
            "Protected Process Light (PPL) for LSASS",
            "EDR rules on LSASS access from non-system processes",
        ],
    ),
    _entry(
        "T1555", "Credentials from Password Stores", "Credential Access",
        """Adversaries steal credentials from password stores (browsers,
        password managers, keychains).""",
        [
            "Access to browser credential store files outside the browser process",
            "Read of macOS Keychain by a non-trusted process",
        ],
        [
            "EDR rules on credential-store file access",
            "Encourage hardware-backed password managers",
        ],
    ),

    # ── Discovery ────────────────────────────────────────────────────────────
    _entry(
        "T1018", "Remote System Discovery", "Discovery",
        """Adversaries enumerate other systems on the network (net view,
        nltest, ping sweeps) to plan lateral movement.""",
        [
            "Burst of net.exe / nltest / nmap activity from a user host",
            "Unusual SMB enumeration from a workstation",
        ],
        [
            "Microsegmentation to limit what one host can scan",
            "Detect mass SMB/RPC enumeration in EDR",
        ],
    ),
    _entry(
        "T1046", "Network Service Discovery", "Discovery",
        """Adversaries scan to identify listening services on a target host
        or network (port scanning, service-version probing).""",
        [
            "Sequential connections to many ports on one host",
            "TCP SYN without ACK follow-up (half-open scan)",
            "ICMP / ARP sweep across a subnet",
        ],
        [
            "IDS / IPS rules for scan signatures",
            "Host firewalls that drop unsolicited probes",
            "Microsegmentation and zero-trust posture",
        ],
    ),
    _entry(
        "T1087", "Account Discovery", "Discovery",
        """Adversaries enumerate accounts (local, domain, cloud) to plan
        which to target next.""",
        [
            "`net user`, `net group`, `whoami /groups` from a user workstation",
            "LDAP enumeration of users / groups",
            "Cloud `list-users` calls from an unusual identity",
        ],
        [
            "Reduce information disclosed by default LDAP/AD queries",
            "Monitor for mass directory enumeration",
        ],
    ),

    # ── Lateral Movement ─────────────────────────────────────────────────────
    _entry(
        "T1021", "Remote Services", "Lateral Movement",
        """Adversaries use legitimate remote services to move laterally - RDP
        (T1021.001), SMB / Admin Shares (T1021.002), SSH (T1021.004),
        WinRM (T1021.006). Often paired with Valid Accounts (T1078).""",
        [
            "RDP login from one workstation to another, not the jump host",
            "SMB connections from a user host to many endpoints",
            "Use of psexec / impacket signatures",
        ],
        [
            "Block RDP / SMB at the host firewall unless allow-listed",
            "Enforce MFA on remote services internally as well",
            "Limit who can `Allow log on through Terminal Services`",
        ],
    ),

    # ── Collection ───────────────────────────────────────────────────────────
    _entry(
        "T1056", "Input Capture", "Collection / Credential Access",
        """Adversaries capture user input (keylogging, GUI input boxes,
        credential-prompt UIs) to harvest credentials or sensitive data.""",
        [
            "Keylogger-like driver or hook installation",
            "Unexpected use of accessibility / input APIs",
        ],
        [
            "EDR rules on raw-input and keyboard-hook APIs",
            "Restrict driver installation to signed, allow-listed drivers",
        ],
    ),
    _entry(
        "T1119", "Automated Collection", "Collection",
        """Adversaries run scripts that automatically harvest files / data of
        interest (documents, source code, secrets).""",
        [
            "Tools recursing through user profiles looking for credential files",
            "Mass read of shared drives by one process",
        ],
        [
            "DLP rules on bulk file access",
            "File-server audit logging for read volume per user",
        ],
    ),

    # ── Command and Control ──────────────────────────────────────────────────
    _entry(
        "T1071", "Application Layer Protocol", "Command and Control",
        """Adversaries communicate with C2 over common application-layer
        protocols (HTTP/S, DNS, mail) to blend with normal traffic.
        Sub-techniques cover specific protocols.""",
        [
            "Beaconing pattern with regular intervals",
            "TLS to unusual SNI on standard ports",
            "DNS TXT queries with long, repeating subdomains",
        ],
        [
            "TLS inspection at the egress proxy",
            "DNS query monitoring and alerting on tunnel indicators",
            "Block known C2 frameworks at the proxy / firewall",
        ],
    ),
    _entry(
        "T1571", "Non-Standard Port", "Command and Control",
        """Adversaries run C2 over a non-standard port to evade simple
        port-based filtering.""",
        [
            "TLS or HTTP traffic on a port that doesn't normally carry it",
            "Outbound traffic to high ports from server hosts",
        ],
        [
            "Strict outbound egress filtering",
            "Protocol-aware inspection (not just port-based)",
        ],
    ),

    # ── Exfiltration ─────────────────────────────────────────────────────────
    _entry(
        "T1041", "Exfiltration Over C2 Channel", "Exfiltration",
        """Adversaries exfiltrate data over the same channel they use for C2,
        reducing the number of detectable connections.""",
        [
            "Sustained outbound bytes on the C2 channel",
            "Large response sizes on what should be small command channels",
        ],
        [
            "Egress data-volume baselining per host",
            "DLP integrated with proxy",
        ],
    ),
    _entry(
        "T1567", "Exfiltration Over Web Service", "Exfiltration",
        """Adversaries exfiltrate data to a legitimate cloud / web service
        (Dropbox, Google Drive, pastebin) to blend with normal traffic.""",
        [
            "Outbound upload volume to a cloud-storage SNI",
            "Use of an unsanctioned cloud-storage account from a corporate host",
        ],
        [
            "CASB / cloud-storage allowlist at the proxy",
            "DLP rules on file uploads to web services",
        ],
    ),

    # ── Impact ───────────────────────────────────────────────────────────────
    _entry(
        "T1486", "Data Encrypted for Impact", "Impact",
        """Adversaries encrypt data on target systems (ransomware) to disrupt
        operations or extort the victim.""",
        [
            "Mass file-rename events across a share",
            "Ransom-note file creation patterns",
            "High-entropy writes by an unusual process",
        ],
        [
            "Immutable, offline backups and tested restore",
            "EDR rules on mass-file-modification behaviour",
            "Network segmentation to slow lateral spread",
        ],
    ),
    _entry(
        "T1490", "Inhibit System Recovery", "Impact",
        """Adversaries delete or disable recovery options (volume shadow
        copies, backup catalogues) to maximise ransomware impact.""",
        [
            "`vssadmin delete shadows /all` execution",
            "`wbadmin delete catalog` execution",
            "Backup-service stop right before file encryption activity",
        ],
        [
            "Restrict / block built-in admin utilities via WDAC",
            "Off-host, immutable backups",
        ],
    ),
]}


VALID_MITRE_IDS = tuple(MITRE_TECHNIQUES.keys())


def get_technique(technique_id: str | None) -> dict | None:
    """Return the entry for an exact match, or None.

    Sub-technique inputs like `T1021.001` fall back to the parent (`T1021`)
    when the sub is not curated separately - the caller can show the parent
    plus a note linking to the sub on attack.mitre.org.
    """
    if not technique_id:
        return None
    tid = technique_id.strip().upper()
    if tid in MITRE_TECHNIQUES:
        return MITRE_TECHNIQUES[tid]
    # Sub-technique: peel the `.NNN` off and try the parent.
    if "." in tid:
        parent = tid.split(".", 1)[0]
        if parent in MITRE_TECHNIQUES:
            entry = dict(MITRE_TECHNIQUES[parent])
            entry["requested_id"] = tid
            entry["sub_technique"] = True
            entry["mitre_url"] = (
                f"https://attack.mitre.org/techniques/{parent}/{tid.split('.', 1)[1]}/"
            )
            return entry
    return None


def all_techniques() -> list[dict]:
    return list(MITRE_TECHNIQUES.values())
