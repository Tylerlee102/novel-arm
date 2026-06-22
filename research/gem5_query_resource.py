import argparse
import json

from gem5.resources.client import get_resource_json_obj


parser = argparse.ArgumentParser()
parser.add_argument("--resource", required=True)
parser.add_argument("--version", default=None)
args = parser.parse_args()

resource = get_resource_json_obj(
    args.resource,
    resource_version=args.version,
)

print(json.dumps(resource, indent=2, sort_keys=True))
