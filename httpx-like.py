import sys
import socket
import argparse


def usage(filename):
    usage_msg = f"""
        Run: python3 {filename} [OPTIONS]

        Example:
            python3 {filename} --remove-headers={{"Authorization","API-KEY"}} --add-header={{"header-name":"header-value"}} -d example.com
        OPTIONS:
            --method                        GET,OPTION,DELETE,HEAD
                --method=GET
            --domain                        Checks liveness of one domain
                --domain=example.com
            --domains                       Checks liveness of multiple domains.
                --domains=domains.txt
            --user-agent                    Changes the default user agent
                --user-agent="agent 1.0"
            --add-headers                   Adds headers to the http request
                --add-headers={{"h1":"v1"}}
            --remove-header                Removes headers except fixed ones
                --remove-header="API-KEY"
            --ports                         Comma seperated ports to make HTTP requests to
                --ports=80
            --output                        Output file to save results to
                --output=out.txt
            --save-2xx                      Only returns results that are in the 2xx level
            --save-3xx                      Only returns results that are in the 3xx level
            --save-4xx                      Only returns results that are in the 4xx level
            --save-5xx                      Only returns results that are in the 5xx level
            --all               
        FIXED HEADERS:
            User-Agent
            Host
    """
    print(usage_msg)


def build_http_header(host, user_agent="httpx-like (prototype)", additional_headers=None, headers_to_remove=None):
    FIXED_HEADERS = ["user-agent", "host"]
    http_headers = {
            "Host": host,
            "User-Agent": user_agent,
            "Connection": "close"
    }
    if additional_headers is not None:
        for k,v in additional_headers:
            http_headers[k] = v

    if headers_to_remove is not None:
        for header in headers_to_remove:
            if not( header.lower() in FIXED_HEADERS):
                http_headers.pop(header, None)

    return http_headers

def parse_arguments(arguments):
    parser = argparse.ArgumentParser(
        prog="probe",
        description="Checks liveness of one or more domains.",
        add_help=True,
    )

    # --- target (one of --domain / --domains required) ---
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--domain",
        help="checks liveness of one domain (e.g. --domain=example.com)",
    )
    target.add_argument(
        "--domains",
        help="file containing one domain per line (e.g. --domains=domains.txt)",
    )

    # --- optional with defaults ---
    parser.add_argument(
        "--method",
        default="GET",
        choices=["GET", "OPTIONS", "OPTION", "DELETE", "HEAD"],
        type=str.upper,
        help="HTTP method (default: GET)",
    )
    parser.add_argument(
        "--user-agent",
        dest="user_agent",
        default="httpx-like (prototype)",
        help="override the default User-Agent",
    )
    parser.add_argument(
        "--ports",
        default="80",
        help="comma-separated ports (default: 80)",
    )
    parser.add_argument(
        "--output",
        help="file to save results to",
    )

    # --- headers ---
    # Accepts JSON: --add-headers='{"h1":"v1","h2":"v2"}'
    parser.add_argument(
        "--add-headers", "--add-header",
        dest="add_headers",
        type=parse_header_json,
        default=None,
        metavar='{"name":"value"}',
        help='extra headers as a JSON object, e.g. --add-headers=\'{"X-Foo":"bar"}\'',
    )
    # Accepts JSON array or comma-separated list: --remove-headers='["Authorization","API-KEY"]'
    parser.add_argument(
        "--remove-headers", "--remove-header",
        dest="remove_headers",
        type=parse_header_list,
        default=None,
        metavar='"Header1,Header2"',
        help='headers to remove, e.g. --remove-headers=Authorization,API-KEY',
    )

    # --- status-code filters (booleans) ---
    parser.add_argument("--save-2xx", dest="save_2xx", action="store_true")
    parser.add_argument("--save-3xx", dest="save_3xx", action="store_true")
    parser.add_argument("--save-4xx", dest="save_4xx", action="store_true")
    parser.add_argument("--save-5xx", dest="save_5xx", action="store_true")
    parser.add_argument(
        "--all",
        dest="save_all",
        action="store_true",
        help="save all status codes (ignores save-Nxx filters)",
    )

    return parser.parse_args(arguments)

def parse_header_json(text):
    """Parse a JSON object into a list of tuples"""

    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise argparse.ArgumentTypeError(f"Invalid JSON for --add-headers: {e}")
    if not isinstance(obj, dict):
        raise argparse.ArgumentTypeError("--add-headers expects a JSON object")
    return list(obj.items())

def parse_header_list(text):
    """Parse a JSON array or comma-separated string into a list of header names."""

    text = text.strip()
    if text.startswith("["):
        try:
            arr = json.loads(text)
        except json.JSONDecodeError as e:
            raise argparse.ArgumentTypeError(f"Invalid JSON for --remove-headers: {e}")
        if not isinstance(arr,list):
            raise argparse.ArgumentTypeError("--remove-headers expects a list")
        return [str(x) for x in arr]
    return [p.strip() for p in text.split(",") if p.strip()]

def main():
    if not (len(sys.argv) >= 2):
        usage(sys.argv[0])
        sys.exit(1)
    
    if len(sys.argv) < 2:
        usage(sys.argv[0])
        sys.exit(1)

    args = parse_arguments(sys.argv[1:])

    if args.domain:
        domains = [args.domain]
    else:
        with open(args.domains) as f:
            domains = [line.strip() for line in f if line.strip()]

    try:
        ports = [int(p) for p in args.ports.split(",") if p.strip()]
    except ValueError:
        sys.exit(f"Invalid --ports value: {args.ports!r}")


    keep = {
        "2xx": args.save_2xx,
        "3xx": args.save_3xx,
        "4xx": args.save_4xx,
        "5xx": args.save_5xx
    }

    if args.save_all or not any(keep.values()):
        keep = {"2xx": True, "3xx": True, "4xx": True, "5xx": True}

    for d in domains:
        headers = build_http_header(
            host=d,
            user_agent=args.user_agent,
            additional_headers=args.add_headers,
            headers_to_remove=args.remove_headers,
        )
        print(d, ports, args.method, headers)



if __name__ == "__main__":
    main()
