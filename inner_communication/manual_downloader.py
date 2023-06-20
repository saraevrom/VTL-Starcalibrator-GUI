import ftplib
from vtl_common.workspace_manager import Workspace


UNPROCESSED_DATA_WORKSPACE = Workspace("unprocessed_data")
def download_vtl(mat_path,season="2022-2023"):
    remote_path = f"TULOMA/Season{season}/"+mat_path
    local_path = UNPROCESSED_DATA_WORKSPACE.get_file(mat_path)
    