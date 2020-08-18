import datetime
import os

import numpy as np
from nengo.utils.matplotlib import rasterplot
import matplotlib.pyplot as plt


class Plotter():
    def __init__( self, trange, rows, cols, dimensions, learning_time, plot_size=(12, 8), dpi=80, dt=0.001 ):
        self.time_vector = trange
        self.plot_sizes = plot_size
        self.dpi = dpi
        self.n_rows = rows
        self.n_cols = cols
        self.n_dims = dimensions
        self.learning_time = learning_time
        self.dt = dt
    
    def plot_results( self, input, pre, post, error, smooth=False, mse=None ):
        fig, axes = plt.subplots( 3, 1, sharex=True, sharey=True, squeeze=False )
        fig.set_size_inches( self.plot_sizes )
        axes[ 0, 0 ].plot(
                self.time_vector,
                input,
                label='Input',
                linewidth=2.0 )
        if self.n_dims <= 3:
            axes[ 0, 0 ].legend(
                    [ f"Input dim {i}" for i in range( self.n_dims ) ],
                    loc='best' )
        axes[ 0, 0 ].set_title( "Input signal", fontsize=16 )
        
        if smooth:
            from scipy.signal import savgol_filter
            
            pre = np.apply_along_axis( savgol_filter, 0, pre, window_length=51, polyorder=3 )
            post = np.apply_along_axis( savgol_filter, 0, post, window_length=51, polyorder=3 )
        
        axes[ 1, 0 ].plot(
                self.time_vector,
                pre,
                linestyle=":",
                label='Pre' )
        axes[ 1, 0 ].set_prop_cycle( None )
        axes[ 1, 0 ].plot(
                self.time_vector,
                post,
                label='Post' )
        if self.n_dims <= 3:
            axes[ 1, 0 ].legend(
                    [ f"Pre dim {i}" for i in range( self.n_dims ) ] +
                    [ f"Post dim {i}" for i in range( self.n_dims ) ],
                    loc='best' )
        axes[ 1, 0 ].set_title( "Pre and post decoded", fontsize=16 )
        
        if smooth:
            from scipy.signal import savgol_filter
            
            error = np.apply_along_axis( savgol_filter, 0, error, window_length=51, polyorder=3 )
        axes[ 2, 0 ].plot(
                self.time_vector,
                error,
                label='Error' )
        if self.n_dims <= 3:
            axes[ 2, 0 ].legend(
                    [ f"Error dim {i}" for i in range( self.n_dims ) ],
                    loc='best' )
        if mse is not None:
            axes[ 2, 0 ].text( 0.85, 0.2, f"MSE: {np.round( mse, 5 )}",
                               horizontalalignment='center',
                               verticalalignment='center',
                               transform=axes[ 2, 0 ].transAxes )
        axes[ 2, 0 ].set_title( "Error", fontsize=16 )
        
        for ax in axes:
            ax[ 0 ].axvline( x=self.learning_time, c="k" )
        
        fig.get_axes()[ 0 ].annotate( f"{self.n_rows} neurons, {self.n_dims} dimensions", (0.5, 0.94),
                                      xycoords='figure fraction', ha='center',
                                      fontsize=20
                                      )
        plt.tight_layout()
        
        return fig
    
    def plot_ensemble_spikes( self, name, spikes, decoded ):
        fig, ax1 = plt.subplots()
        fig.set_size_inches( self.plot_sizes )
        ax1 = plt.subplot( 1, 1, 1 )
        rasterplot( self.time_vector, spikes, ax1 )
        ax1.axvline( x=self.learning_time, c="k" )
        ax2 = plt.twinx()
        ax2.plot( self.time_vector, decoded, c="k", alpha=0.3 )
        ax1.set_xlim( 0, max( self.time_vector ) )
        ax1.set_ylabel( 'Neuron' )
        ax1.set_xlabel( 'Time (s)' )
        fig.get_axes()[ 0 ].annotate( name + " neural activity", (0.5, 0.94),
                                      xycoords='figure fraction', ha='center',
                                      fontsize=20
                                      )
        
        return fig
    
    def plot_values_over_time( self, pos_memr, neg_memr ):
        fig, axes = plt.subplots( self.n_rows, self.n_cols )
        fig.set_size_inches( self.plot_sizes )
        for i in range( axes.shape[ 0 ] ):
            for j in range( axes.shape[ 1 ] ):
                pos_cond = pos_memr[ ..., i, j ]
                neg_cond = neg_memr[ ..., i, j ]
                axes[ i, j ].plot( pos_cond, c="r" )
                axes[ i, j ].plot( neg_cond, c="b" )
                axes[ i, j ].set_title( f"{j}->{i}" )
                axes[ i, j ].set_yticklabels( [ ] )
                axes[ i, j ].set_xticklabels( [ ] )
                plt.subplots_adjust( hspace=0.7 )
        fig.get_axes()[ 0 ].annotate( "Conductances over time", (0.5, 0.94),
                                      xycoords='figure fraction', ha='center',
                                      fontsize=20
                                      )
        # plt.tight_layout()
        
        return fig
    
    def plot_weights_over_time( self, pos_memr, neg_memr ):
        fig, axes = plt.subplots( self.n_rows, self.n_cols )
        fig.set_size_inches( self.plot_sizes )
        for i in range( axes.shape[ 0 ] ):
            for j in range( axes.shape[ 1 ] ):
                pos_cond = 1 / pos_memr[ ..., i, j ]
                neg_cond = 1 / neg_memr[ ..., i, j ]
                axes[ i, j ].plot( pos_cond - neg_cond, c="g" )
                axes[ i, j ].set_title( f"{j}->{i}" )
                axes[ i, j ].set_yticklabels( [ ] )
                axes[ i, j ].set_xticklabels( [ ] )
                plt.subplots_adjust( hspace=0.7 )
        fig.get_axes()[ 0 ].annotate( "Weights over time", (0.5, 0.94),
                                      xycoords='figure fraction', ha='center',
                                      fontsize=20
                                      )
        # plt.tight_layout()
        
        return fig
    
    def plot_weight_matrices_over_time( self, weights, n_cols=5, sample_every=0.001 ):
        n_rows = int( self.learning_time / n_cols ) + 1
        fig, axes = plt.subplots( n_rows, n_cols )
        fig.set_size_inches( self.plot_sizes )
        
        for t, ax in enumerate( axes.flatten() ):
            if t <= self.learning_time:
                ax.matshow( weights[ int( (t / self.dt) / (sample_every / self.dt) ), ... ],
                            cmap=plt.cm.Blues )
                ax.set_title( f"{t}" )
                ax.set_yticklabels( [ ] )
                ax.set_xticklabels( [ ] )
                plt.subplots_adjust( hspace=0.7 )
            else:
                ax.set_axis_off()
        fig.get_axes()[ 0 ].annotate( "Weights over time", (0.5, 0.94),
                                      xycoords='figure fraction', ha='center',
                                      fontsize=18
                                      )
        # plt.tight_layout()
        
        return fig


def generate_sines( dimensions ):
    # iteratively build phase shifted sines
    s = "lambda t: ("
    phase_shift = (2 * np.pi) / dimensions
    for i in range( dimensions ):
        s += f"np.sin( 1 / 4 * 2 * np.pi * t + {i * phase_shift}),"
    s += ")"
    
    return eval( s )


def make_timestamped_dir( root=None ):
    if root is None:
        root = "../data/"
    
    time_string = datetime.datetime.now().strftime( "%d-%m-%Y_%H-%M" )
    dir_name = root + time_string + "/"
    if os.path.isdir( dir_name ):
        dir_name = dir_name[ :-1 ]
        minutes = str( int( dir_name[ -1 ] ) + 1 )
        dir_name = dir_name[ :-1 ] + minutes + "/"
    dir_images = dir_name + "images/"
    os.mkdir( dir_name )
    os.mkdir( dir_images )
    
    return dir_name, dir_images


def gini( array ):
    """Calculate the Gini coefficient of exponent numpy array."""
    # based on bottom eq:
    # http://www.statsdirect.com/help/generatedimages/equations/equation154.svg
    # from:
    # http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
    # All values are treated equally, arrays must be 1d:
    array = array.flatten()
    if np.amin( array ) < 0:
        # Values cannot be negative:
        array -= np.amin( array )
    # Values cannot be 0:
    array += 0.0000001
    # Values must be sorted:
    array = np.sort( array )
    # Index per array element:
    index = np.arange( 1, array.shape[ 0 ] + 1 )
    # Number of array elements:
    n = array.shape[ 0 ]
    # Gini coefficient:
    return ((np.sum( (2 * index - n - 1) * array )) / (n * np.sum( array )))


def save_weights( path, probe ):
    np.save( path + "weights.npy", probe[ -1 ].T )


def save_memristors_to_csv( dir, pos_memr, neg_memr ):
    pos_memr = pos_memr.reshape( (pos_memr.shape[ 0 ], -1) )
    neg_memr = neg_memr.reshape( (neg_memr.shape[ 0 ], -1) )
    
    header = [ ]
    for i in range( pos_memr.shape[ 1 ] ):
        for j in range( pos_memr.shape[ 1 ] ):
            header.append( f"{j}->{i}" )
    header = ','.join( header )
    
    np.savetxt( dir + "pos_resistances.csv", pos_memr, delimiter=",", header=header, comments="" )
    np.savetxt( dir + "neg_resistances.csv", neg_memr, delimiter=",", header=header, comments="" )
    np.savetxt( dir + "weights.csv", 1 / pos_memr - 1 / neg_memr, delimiter=",", header=header, comments="" )


def save_results_to_csv( dir, input, pre, post, error ):
    header = [ ]
    header.append( ",".join( [ "input" + str( i ) for i in range( input.shape[ 1 ] ) ] ) )
    header.append( ",".join( [ "pre" + str( i ) for i in range( pre.shape[ 1 ] ) ] ) )
    header.append( ",".join( [ "post" + str( i ) for i in range( post.shape[ 1 ] ) ] ) )
    header.append( ",".join( [ "error" + str( i ) for i in range( error.shape[ 1 ] ) ] ) )
    header = ",".join( header )
    
    with open( dir + "results.csv", "w" ) as f:
        np.savetxt( f, np.hstack( (input, pre, post, error) ), delimiter=",", header=header, comments="" )
