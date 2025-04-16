#%% 
from Metatree_functions_common import *

from tap import Tap

class myargs(Tap):
    env:str = ".env_debug" # the environment file to load the settings from
    
# import sys 
# sys.argv = ['arg0','--env','.env_science']


args = myargs().parse_args()

#importConfiguration(".env_local")
#importConfiguration(".env_debug")
importConfiguration(args.env)

print(f"loading settings from {args.env}")

#%% initialize settings
def initializeDatabase():
    print("initializating database...")
    print("patching plant species")
    patch_bulk_meta_data("./plant_species.ttl")
    print("patching other species")
    patch_meta_data("./other_species.ttl")
    print("patching growth facilties")
    patch_meta_data("./growth_facilities.ttl")
    patch_meta_data("./plant_growth_medium.ttl")
    patch_meta_data("./ploidy.ttl")
    patch_meta_data("./growth_facilities.ttl")
    patch_meta_data("./plant_states_stages.ttl")

    patch_meta_data("./apparatus.ttl")
    patch_meta_data("./assay_types.ttl")
    patch_meta_data("./treatments.ttl")
    patch_meta_data("./extra_plant_species.ttl")

#%%

initializeDatabase()

# %%
