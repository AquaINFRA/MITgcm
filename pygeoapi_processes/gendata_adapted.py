# Modified copy of the gendata.py file here:
# MITgcm/verification/tutorial_baroclinic_gyre/input/
#
# This script was modified to be able to call it as a function
# from another python script. The purpose of this is to run
# the baroclinic gyre tutorial, including gendata.py, as a
# OGC processing service on a server, using the pygeoapi platform,
# to be called by users via HTTP.
# This is done in the scope of the EU-funded research project
# AquaINFRA (aquainfra.eu).
#
# Merret Buurman (IGB Berlin), October 2024


import numpy as np
from numpy import cos, pi
import logging
import os
LOGGER = logging.getLogger(__name__)


def gendata(out_path='./', Ho=1800, nx=62, ny=62, xo=0, yo=15, dx=1, dy=1, tauMax=0.1, Tmin=0, Tmax=30, LOGGER=None):

    if not LOGGER is None:
        LOGGER.info('Running adapted gendata.py...')
        LOGGER.info('Current working directory: %s' % os.getcwd())
        LOGGER.info('Contents of cwd: %s' % os.listdir())

    xeast  = xo + (nx-2)*dx   # eastern extent of ocean domain
    ynorth = yo + (ny-2)*dy   # northern extent of ocean domain

    # Flat bottom at z=-Ho
    h = -Ho * np.ones((ny, nx))

    # create a border ring of walls around edge of domain
    h[:, [0,-1]] = 0   # set ocean depth to zero at east and west walls
    h[[0,-1], :] = 0   # set ocean depth to zero at south and north walls
    # save as single-precision (float32) with big-endian byte ordering
    outfile_bathy = out_path.rstrip('/')+'/bathy.bin'

    if LOGGER is not None:
        LOGGER.info('Writing bathyFile: %s' % outfile_bathy)

    h.astype('>f4').tofile(outfile_bathy)

    # ocean domain extends from (xo,yo) to (xeast,ynorth)
    # (i.e. the ocean spans nx-2, ny-2 grid cells)
    # out-of-box-config: xo=0, yo=15, dx=dy=1 deg, ocean extent (0E,15N)-(60E,75N)
    # model domain includes a land cell surrounding the ocean domain
    # The full model domain cell centers are located at:
    #    XC(:,1) = -0.5, +0.5, ..., +60.5 (degrees longitiude)
    #    YC(1,:) = 14.5, 15.5, ..., 75.5 (degrees latitude)
    # and full model domain cell corners are located at:
    #    XG(:,1) = -1,  0, ..., 60 [, 61] (degrees longitiude)
    #    YG(1,:) = 14, 15, ..., 75 [, 76] (degrees latitude)
    # where the last value in brackets is not included 
    # in the MITgcm grid variables XG,YG (but is in variables Xp1,Yp1)
    # and reflects the eastern and northern edge of the model domain respectively.
    # See section 2.11.4 of the MITgcm users manual.

    # Zonal wind-stress
    x = np.linspace(xo-dx, xeast, nx)
    y = np.linspace(yo-dy, ynorth, ny) + dy/2
    Y, X = np.meshgrid(y, x, indexing='ij')     # zonal wind-stress on (XG,YC) points
    tau = -tauMax * cos(2*pi*((Y-yo)/(ny-2)/dy))  # ny-2 accounts for walls at N,S boundaries
    outfile_windx_cosy = out_path.rstrip('/')+'/windx_cosy.bin'

    if LOGGER is not None:
        LOGGER.info('Writing zonalWindFile: %s' % outfile_windx_cosy)

    tau.astype('>f4').tofile(outfile_windx_cosy)

    # Restoring temperature (function of y only,
    # from Tmax at southern edge to Tmin at northern edge)
    Tmax = 30
    Tmin = 0
    Trest = (Tmax-Tmin)/(ny-2)/dy * (ynorth-Y) + Tmin # located and computed at YC points
    outfile_SST_relax = out_path.rstrip('/')+'/SST_relax.bin'

    if LOGGER is not None:
        LOGGER.info('Writing thetaClimFile: %s' % outfile_SST_relax)

    Trest.astype('>f4').tofile(outfile_SST_relax)


if __name__ == '__main__':

    Ho = 1800  # depth of ocean (m)
    nx = 62    # gridpoints in x
    ny = 62    # gridpoints in y
    xo = 0     # origin in x,y for ocean domain
    yo = 15    # (i.e. southwestern corner of ocean domain)
    dx = 1     # grid spacing in x (degrees longitude)
    dy = 1     # grid spacing in y (degrees latitude)
    tauMax = 0.1 # Zonal wind-stress
    Tmin = 0
    Tmax = 30

    out_path = '.'
    gendata(out_path=out_path, Ho=Ho, nx=nx, ny=ny, xo=xo, yo=yo, dx=dx, dy=dy, tauMax=tauMax, Tmin=Tmin, Tmax=Tmax, LOGGER=LOGGER)

    # Note:
    # This script writes three files, whose names are defined here:
    # https://github.com/MITgcm/MITgcm/blob/master/verification/tutorial_baroclinic_gyre/input/data
    # See:
    #   bathyFile='bathy.bin',
    #   zonalWindFile='windx_cosy.bin',
    #   thetaClimFile='SST_relax.bin',
