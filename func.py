import io
import json
from fdk import response

import oci


def handler(ctx, data: io.BytesIO = None):

    resp = None

    try:
        signer = oci.auth.signers.get_resource_principals_signer()
        searches = oci.resource_search.ResourceSearchClient(
            config={}, signer=signer)
        search_details = oci.resource_search.models.StructuredSearchDetails(
            type="Structured",
            query="query instance resources where (definedTags.namespace = 'autoschedule' && definedTags.key = 'AUTOSCHEDULE'  && definedTags.value = 'TRUE')",
        )
        search_matches = searches.search_resources(
            search_details=search_details)
        computes = search_matches.data.items
        print("Compute OCID: {0}".format(computes), flush=True)
        for compute in computes:
            print("Compute OCID: {0}".format(compute.identifier), flush=True)
            instanceId = compute.identifier
            resp = perform_action(signer, instanceId, "STOP")

        return response.Response(
            ctx,
            response_data=json.dumps(resp),
            headers={"Content-Type": "application/json"},
        )
    except (Exception, ValueError) as e:
        print("Error " + str(e), flush=True)


def perform_action(signer, instanceId, action):

    compute_client = oci.core.ComputeClient(config={}, signer=signer)
    print("Performing action", flush=True)
    try:
        if compute_client.get_instance(instanceId).data.lifecycle_state in ("RUNNING"):
            try:

                resp = compute_client.instance_action(instanceId, action)
                print("response code: {0}".format(resp.status), flush=True)
            except oci.exceptions.ServiceError as e:
                print("Action failed. {0}".format(e), flush=True)
                raise
        else:
            print(
                "The instance {0} was in the incorrect state to stop".format(
                    instanceId
                ),
                flush=True,
            )
    except oci.exceptions.ServiceError as e:
        print("Action failed. {0}".format(e), flush=True)
        raise

    print(
        "Action " + action + " performed on instance: {}".format(instanceId), flush=True
    )

    return compute_client.get_instance(instanceId).data.lifecycle_state
