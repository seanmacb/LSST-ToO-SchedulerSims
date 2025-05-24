from rubin_scheduler.scheduler.example import example_scheduler
from rubin_scheduler.scheduler.schedulers import core_scheduler
import numpy as np
import healpy as hp
import healsparse
import os
from rubin_scheduler.scheduler.utils import SimTargetooServer, TargetoO
from rubin_scheduler.scheduler.model_observatory import ModelObservatory

from rubin_scheduler.scheduler import sim_runner
from rubin_scheduler.scheduler.surveys.too_scripted_surveys import ToOScriptedSurvey

import rubin_scheduler.scheduler.basis_functions as basis_functions
import matplotlib.pylab as plt

def main():
    exsched = example_scheduler()

    bf_list = []
    bf_list.append(basis_functions.AvoidDirectWind(wind_speed_maximum=20, nside=32))
    bf_list.append(basis_functions.MoonAvoidanceBasisFunction(moon_distance=30.0))

    # load up the example scheduler, which has ToO surveys included by default
    scheduler = core_scheduler.CoreScheduler(exsched.survey_lists)

    nside = 32
    observatory = ModelObservatory(nside=nside,)# sim_to_o=sim_to_o)

    vec = hp.ang2vec(1.5*np.pi / 2, np.pi * 0 / 4)
    # ipix_disc = hp.query_disc(nside=nside, vec=vec, radius=np.radians(4)) # This makes a ~50 deg^2 area
    ipix_disc = hp.query_disc(nside=nside, vec=vec, radius=np.radians(2)) # This makes a ~12 deg^2 area
    # ipix_disc = hp.query_disc(nside=nside, vec=vec, radius=np.radians(10)) # This makes a ~314 deg^2 area
    

    # Make a ToO event here

    # Make a healpix map, can be any nside
    footprint = np.zeros(hp.nside2npix(nside))
    # # Set some healpix near the pole to be where to observe
    # footprint[-8:] = 1
    footprint[ipix_disc] =1
    
    # Set the event to go off at the start of the survey
    event_start = observatory.mjd + 4 + 14
    print("MJD of event start:",event_start)
    duration = 5 # Days
    
    # Need to set a nominal center for the event
    # could just take mean of RA,dec HEALpix map I suppose
    ra_deg = 45.
    dec_deg = -45.
    
    # ToO type. Should probabably document the 
    # options for this somewhere.
    too_type = "BBH_case_A" 
    
    # Unique int ID for each event
    target_id = 100
    
    event = TargetoO(
                    target_id,
                    footprint,
                    event_start,
                    duration,
                    ra_rad_center=np.radians(ra_deg),
                    dec_rad_center=np.radians(dec_deg),
                    too_type=too_type,
                    posterior_distance=2.2E6)
    # Thing to pass to the ModelObservatory so it will send out
    # the ToO alert in the Conditions object
    sim_to_o = SimTargetooServer([event])

    # model observatory with the ToO ready to go
    observatory =  ModelObservatory(nside=nside, sim_to_o=sim_to_o, downtimes="ideal", cloud_data="ideal",)

    # simulate for N days
    observatory, scheduler, observations = sim_runner(
            observatory,
            scheduler,
            sim_duration=np.array([44.0])+14,
            filename=None,
            verbose=True,
        )

    print("Scheduler note: {}".format(np.unique(observations["scheduler_note"],return_counts=True)))

    fig = makeObsPositions(observations)
    fig.savefig(os.path.join(os.getcwd(),"figures","obsPlot.png"),dpi=180)

    too_indx = ["ToO" in note for note in observations["scheduler_note"]]

    ToOObservations = observations[too_indx]
    colsOfInterest = ["RA","dec","mjd","exptime","band","filter","nexp","airmass","night","visittime","scheduler_note"]

    fig=makeFilterDist(ToOObservations)
    fig.savefig(os.path.join(os.getcwd(),"figures","filterPlot.png"),dpi=180)

    return 0
    
def makeFilterDist(observations):
    fig,axs = plt.subplots(1,len(np.unique(observations[:]["night"])),figsize=(5*len(np.unique(observations[:]["night"])),5),sharey=True)
    for num,ax in zip(np.unique(observations[:]["night"]),axs.flatten()):
    # for num in np.unique(observations[:]["night"]):
        strin = "Exposure times: {}".format(np.unique(observations["exptime"][[t==num for t in observations[:]["night"]]]))
        subset = observations[:][[t==num for t in observations[:]["night"]]]
        ax.scatter(subset[:]["mjd"]-60980-num,subset[:]["band"],s=subset[:]["exptime"])
        ax.set_title("Night {}\n{}".format(num,strin))
    return fig

def makeObsPositions(observations):
    # Check that ToO events are where we think they should be
    too_indx = ["ToO" in note for note in observations["scheduler_note"]]
    
    fig, ax = plt.subplots()
    
    ax.scatter(np.degrees(observations["RA"]), np.degrees(observations["dec"]), color='black',label="Other observations")
    ax.scatter(np.degrees(observations["RA"][too_indx]), np.degrees(observations["dec"][too_indx]), color="red",label="ToO Observations")
    
    ax.set_xlabel("RA (deg)")
    ax.set_ylabel("Dec (deg)")
    ax.legend()
    ax.set_title("ToO observations for test: BBH, dark conditions, distant event")
    
    return fig

if __name__=="__main__":
    main()