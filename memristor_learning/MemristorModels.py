import numpy as np


class MemristorPair:
    def __init__( self ):
        self.mem_plus = None
        self.mem_minus = None
    
    def pulse( self, adj, value, method, scaled=True ):
        raise NotImplementedError
    
    def get_state( self, value, scaled ):
        return (self.mem_plus.get_state( value, scaled ) - self.mem_minus.get_state( value, scaled ))
    
    def save_state( self ):
        self.mem_plus.save_state()
        self.mem_minus.save_state()
    
    def plot_state( self, value, i, j, range, ax, c, combined=False ):
        if value == "resistance":
            tmp_plus = self.mem_plus.history
            tmp_minus = self.mem_minus.history
        if value == "conductance":
            tmp_plus = np.divide( 1, self.mem_plus.history )
            tmp_minus = np.divide( 1, self.mem_minus.history )
        ax.plot( range, tmp_plus, c="r", label='Excitatory' )
        ax.plot( range, tmp_minus, c="b", label='Inhibitory' )
        if not combined:
            ax.annotate( str( j + 1 ) + "->" + str( i + 1 ), xy=(range[ 0 ], tmp_plus[ 0 ]), c="r" )
            ax.annotate( str( j + 1 ) + "->" + str( i + 1 ), xy=(range[ 0 ], tmp_minus[ 0 ]), c="b" )
        if combined:
            ax.set_title( str( j + 1 ) + "->" + str( i + 1 ) )
            ax.label_outer()
            ax.set_yticklabels( [ ] )


class MemristorAnoukPair( MemristorPair ):
    def __init__( self ):
        super().__init__()
        # instantiate memristor pair
        self.mem_plus = MemristorAnouk()
        self.mem_minus = MemristorAnouk()
    
    def pulse( self, adj, value, method, scaled=True ):
        if method == "same":
            if adj > 0:
                self.mem_plus.pulse()
            if adj < 0:
                self.mem_minus.pulse()
        if method == "inverse":
            if adj < 0:
                self.mem_plus.pulse()
            if adj > 0:
                self.mem_minus.pulse()
        
        return self.mem_plus.get_state( value, scaled ) - self.mem_minus.get_state( value, scaled )


class Memristor:
    def __init__( self ):
        self.n = 0
        # save resistance history for later analysis
        self.history = [ ]
        
        self.r_curr = None
        self.r_max = None
        self.r_min = None
    
    def pulse( self, V ):
        raise NotImplementedError
    
    def get_state( self, value="conductance", scaled=True, gain=10**4 ):
        epsilon = np.finfo( float ).eps
        
        if value == "conductance":
            g_curr = 1.0 / self.r_curr
            g_min = 1.0 / self.r_max
            g_max = 1.0 / self.r_min
            if scaled:
                ret_val = ((g_curr - g_min) / (g_max - g_min)) + epsilon
            else:
                ret_val = g_curr + epsilon
        
        if value == "resistance":
            if scaled:
                ret_val = ((self.r_curr - self.r_min) / (self.r_max - self.r_min)) + epsilon
            else:
                ret_val = self.r_curr + epsilon
        
        return gain * ret_val
    
    def save_state( self ):
        self.history.append( self.r_curr )
    
    def plot_state( self, value, i, j, range, ax, c ):
        if value == "resistance":
            tmp = self.history
        if value == "conductance":
            tmp = np.divide( 1.0, self.history )
        
        ax.plot( range, tmp, c=c )
        ax.annotate( "(" + str( i ), xy=(10, 10) )


class MemristorAnouk( Memristor ):
    def __init__( self, r0=100, r1=2.5 * 10**8, a=-0.128, b=-0.522 ):
        super().__init__()
        # set parameters of device
        self.r_min = r0
        self.r_max = r1
        self.a = a
        self.b = b
        
        # Weight initialisation
        import random
        self.r_curr = random.uniform( 10**8, 2.5 * 10**8 )
        # self.r_curr = self.r_max
    
    # pulse the memristor with a tension
    def pulse( self, V=1e-1 ):
        c = self.a + self.b * V
        self.r_curr = self.r_min + self.r_max * (((self.r_curr - self.r_min) / self.r_max)**(1 / c) + 1)**c
        
        return self.r_curr
    
    def plot_memristor_curve_exhaustive( self, V=1, threshold=1000, step=10 ):
        import matplotlib.pyplot as plt
        import sys, time
        
        c = self.a + self.b * V
        
        x = [ ]
        y = [ ]
        n = 1
        r_curr = self.r_max
        it = 1
        
        start_time = time.time()
        while r_curr >= self.r_min + threshold:
            x.append( n )
            y.append( r_curr )
            
            n += step
            it += 1
            r_curr = self.r_min + self.r_max * n**c
            sys.stdout.write( f"\rIteration {it}: "
                              f"resistance {self.r_max}/{round( r_curr, 2 )}/{self.r_min} + {threshold} threshold"
                              f", step {step}" )
            sys.stdout.flush()
        end_time = time.time()
        print( f"\n{round( end_time - start_time, 2 )} seconds elapsed" )
        
        plt.plot( x, y )
        plt.yscale( 'log' )
        plt.xlabel( "Pulses (n)" )
        plt.ylabel( "Resistance (R)" )
        plt.grid( alpha=.4, linestyle='--' )
        plt.show()
    
    def plot_memristor_curve_interpolate( self, V=1, threshold=1000 ):
        import matplotlib.pyplot as plt
        from math import fabs, floor
        
        c = self.a + self.b * V
        
        x = [ ]
        y = [ ]
        n = 0
        step = 1
        r_curr = self.r_max
        
        from tqdm import tqdm
        with tqdm( total=self.r_max - (self.r_min + threshold) ) as pbar:
            r_pre = r_curr
            n += step
            r_curr = self.r_min + self.r_max * n**c
            r_diff = fabs( r_curr - r_pre )
            step += floor( 1 / r_diff )
            
            x.append( n )
            y.append( r_curr )
            
            pbar.update( n )
        
        def expand_interpolate( oldx, oldy ):
            from scipy.interpolate import interp1d
            
            try:
                if oldx[ 1 ] - oldx[ 0 ] <= 1:
                    return oldx[ 1 ] - oldx[ 0 ], None, None
                
                expanded_interval = np.arange( oldx[ 0 ], oldx[ 1 ] + 1 )
                f = interp1d( oldx, oldy )
                
                return oldx[ 1 ] - oldx[ 0 ], expanded_interval[ 1:-1 ], f( expanded_interval[ 1:-1 ] )
            except IndexError:
                return oldx[ 0 ], None, None
        
        c = 0
        
        with tqdm( total=x[ -1 ] ) as pbar:
            while c < len( x ):
                int_length, newx, newy = expand_interpolate( x[ c:c + 2 ], y[ c:c + 2 ] )
                if newx is not None:
                    for cc, (xx, yy) in enumerate( zip( newx, newy ) ):
                        x.insert( c + cc + 1, xx )
                        y.insert( c + cc + 1, yy )
                c += int_length
                pbar.update( int_length )
        
        plt.plot( x, y )
        plt.yscale( 'log' )
        plt.xlabel( "Pulses (n)" )
        plt.ylabel( "Resistance (R)" )
        plt.grid( alpha=.4, linestyle='--' )
        plt.show()
