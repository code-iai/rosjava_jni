/*
 * Software License Agreement (BSD License)
 *
 *  Copyright (c) 2008, Willow Garage, Inc.
 *  All rights reserved.
 *
 *  Redistribution and use in source and binary forms, with or without
 *  modification, are permitted provided that the following conditions
 *  are met:
 *
 *   * Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *   * Redistributions in binary form must reproduce the above
 *     copyright notice, this list of conditions and the following
 *     disclaimer in the documentation and/or other materials provided
 *     with the distribution.
 *   * Neither the name of Willow Garage, Inc. nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 *  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 *  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 *  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 *  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 *  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 *  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 *  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 *  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *  POSSIBILITY OF SUCH DAMAGE.
 */

// author: Jason Wolfe


package ros;

import java.util.HashMap;
import java.util.Map;

import ros.communication.Time;
import ros.roscpp.RosCpp;

// Interface type to make handling multiple implementations easier
public abstract class Ros {
    private static class SingletonHolder { 
      private static final Ros instance = RosCpp.getInstance();
    }
    
    public static Ros getInstance() {return SingletonHolder.instance; }

    public abstract void init(String name, boolean noSigintHandler, boolean anonymousName, boolean noRosout, String [] args);
    public void init(String name) { init(name, false, false, false, new String[0]); }

  public abstract boolean isInitialized();

  public abstract boolean ok();

	public abstract NodeHandle createNodeHandle(String ns, Map<String, String> remappings);

	public abstract Time now();

	public abstract void spin();
	
	public abstract void spinOnce();

	public abstract void logDebug(String message);
	public abstract void logInfo(String message);
	public abstract void logWarn(String message);
	public abstract void logError(String message);
	public abstract void logFatal(String message);
	
	public abstract String getPackageLocation(String pkgName); 
	
	// Convenience methods, defined as described in node_handle.h.
	
	public NodeHandle createNodeHandle() { 
		return createNodeHandle(""); 
	}
	
	public NodeHandle createNodeHandle(String ns) { 
		return createNodeHandle(ns, new HashMap<String, String>()); 
	}

	public NodeHandle createNodeHandle(NodeHandle parent, String ns) { 
		return createNodeHandle(parent.getNamespace() + "/" + ns); 
	}
	
	public NodeHandle createNodeHandle(NodeHandle parent, String ns, Map<String, String> remappings) {
		return createNodeHandle(parent.getNamespace() + "/" + ns, remappings);
	}	
}
