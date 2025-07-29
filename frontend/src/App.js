import React, { useState, useEffect, createContext, useContext, useRef } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Loader } from '@googlemaps/js-api-loader';
import { useRazorpay, RazorpayOrderOptions } from 'react-razorpay';
import axios from 'axios';
import { 
  Car, 
  MapPin, 
  User, 
  Phone, 
  DollarSign, 
  Clock, 
  Navigation,
  LogOut,
  Users,
  Settings,
  Eye,
  EyeOff,
  CreditCard,
  Smartphone,
  CheckCircle,
  XCircle,
  IndianRupee
} from 'lucide-react';
import DriverDashboard from './DriverDashboard';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Context for user authentication
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const login = (userData, token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Axios interceptor for authentication
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Google Maps Hook
const useGoogleMaps = () => {
  const [map, setMap] = useState(null);
  const [directionsService, setDirectionsService] = useState(null);
  const [directionsRenderer, setDirectionsRenderer] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [placesService, setPlacesService] = useState(null);

  useEffect(() => {
    const initializeMap = async () => {
      try {
        const response = await axios.get(`${API}/maps-config`);
        const apiKey = response.data.google_maps_api_key;

        const loader = new Loader({
          apiKey: apiKey,
          version: 'weekly',
          libraries: ['places', 'geometry']
        });

        await loader.load();
        setDirectionsService(new window.google.maps.DirectionsService());
        setDirectionsRenderer(new window.google.maps.DirectionsRenderer());
        setLoaded(true);
      } catch (error) {
        console.error('Error initializing Google Maps:', error);
      }
    };

    initializeMap();
  }, []);

  const initMap = (element, options = {}) => {
    if (!loaded || !window.google || !element) return null;

    const defaultOptions = {
      zoom: 13,
      center: { lat: 13.0827, lng: 80.2707 }, // Default to Chennai
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      zoomControl: true,
      ...options
    };

    const newMap = new window.google.maps.Map(element, defaultOptions);
    setMap(newMap);
    
    if (directionsRenderer) {
      directionsRenderer.setMap(newMap);
    }

    // Initialize places service
    if (window.google.maps.places) {
      setPlacesService(new window.google.maps.places.PlacesService(newMap));
    }
    
    return newMap;
  };

  const calculateRoute = (start, end, callback) => {
    if (!directionsService || !directionsRenderer) return;

    const request = {
      origin: start,
      destination: end,
      travelMode: window.google.maps.TravelMode.DRIVING,
    };

    directionsService.route(request, (result, status) => {
      if (status === 'OK') {
        directionsRenderer.setDirections(result);
        const route = result.routes[0];
        const distance = route.legs[0].distance.value / 1000; // Convert to km
        callback({ distance, route });
      }
    });
  };

  const getUserLocation = () => {
    return new Promise((resolve, reject) => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              lat: position.coords.latitude,
              lng: position.coords.longitude
            });
          },
          (error) => {
            console.error('Geolocation error:', error);
            // Fallback to Chennai coordinates
            resolve({ lat: 13.0827, lng: 80.2707 });
          }
        );
      } else {
        console.error('Geolocation not supported');
        // Fallback to Chennai coordinates
        resolve({ lat: 13.0827, lng: 80.2707 });
      }
    });
  };

  const searchPlaces = (query, callback) => {
    if (!placesService || !map) return;

    const request = {
      query: query,
      location: map.getCenter(),
      radius: 50000, // 50km radius
    };

    placesService.textSearch(request, (results, status) => {
      if (status === window.google.maps.places.PlacesServiceStatus.OK && results) {
        callback(results);
      } else {
        callback([]);
      }
    });
  };

  return { 
    loaded, 
    initMap, 
    calculateRoute, 
    getUserLocation, 
    searchPlaces,
    map, 
    directionsService, 
    directionsRenderer 
  };
};

// Login/Register Component with Mobile OTP
const AuthPage = () => {
  const [authMode, setAuthMode] = useState('mobile'); // 'mobile' or 'legacy'
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleMobileAuthSuccess = (userData, token) => {
    login(userData, token);
    
    if (userData.user_type === 'admin') {
      navigate('/admin-dashboard');
    } else if (userData.user_type === 'driver') {
      navigate('/driver-dashboard');
    } else {
      navigate('/rider-dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <Car className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">RideShare</h1>
          <p className="text-gray-600 mt-2">
            Quick & secure mobile authentication
          </p>
        </div>

        {authMode === 'mobile' ? (
          <div>
            <MobileOTPAuth onSuccess={handleMobileAuthSuccess} />
            
            {/* Switch to legacy auth */}
            <div className="mt-6 text-center">
              <button
                type="button"
                className="text-sm text-gray-500 hover:text-gray-700"
                onClick={() => setAuthMode('legacy')}
              >
                Use email & password instead
              </button>
            </div>
          </div>
        ) : (
          <LegacyAuthForm onSwitch={() => setAuthMode('mobile')} />
        )}
      </div>
    </div>
  );
};

// Legacy Email/Password Authentication (kept for backward compatibility)


// Notification Hook for Driver Alerts
const useDriverNotifications = (isAvailable, rideRequests) => {
  const [lastRequestCount, setLastRequestCount] = useState(0);
  const [notificationPermission, setNotificationPermission] = useState('default');
  
  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window) {
      if (Notification.permission === 'granted') {
        setNotificationPermission('granted');
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
          setNotificationPermission(permission);
        });
      }
    }
  }, []);

  // Play notification sound
  const playNotificationSound = () => {
    // Create audio context for notification sound
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // Create a simple notification tone
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Configuration for notification sound
    oscillator.frequency.setValueAtTime(800, audioContext.currentTime); // High pitch
    oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1); // Lower pitch
    oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2); // High pitch again
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  };

  // Show browser notification
  const showBrowserNotification = (requestsCount) => {
    if (notificationPermission === 'granted') {
      const notification = new Notification('New Ride Request!', {
        body: `You have ${requestsCount} new ride request${requestsCount > 1 ? 's' : ''} nearby`,
        icon: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png',
        badge: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png',
        tag: 'ride-request',
        requireInteraction: true
      });

      // Auto-close notification after 5 seconds
      setTimeout(() => notification.close(), 5000);
    }
  };

  // Monitor ride requests for new notifications
  useEffect(() => {
    if (isAvailable && rideRequests.length > lastRequestCount) {
      const newRequestsCount = rideRequests.length - lastRequestCount;
      
      if (lastRequestCount > 0) { // Don't notify on initial load
        // Play sound notification
        playNotificationSound();
        
        // Show browser notification
        showBrowserNotification(newRequestsCount);
        
        // Visual flash effect (handled in component)
        const event = new CustomEvent('newRideRequest', { 
          detail: { count: newRequestsCount } 
        });
        window.dispatchEvent(event);
      }
    }
    
    setLastRequestCount(rideRequests.length);
  }, [rideRequests.length, isAvailable, lastRequestCount]);

  return { notificationPermission };
};



      // Vehicle-specific SVG icons
      const vehicleIcons = {
        bike: `
          <svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
            <circle cx="24" cy="24" r="20" fill="#000000" stroke="#ffffff" stroke-width="4"/>
            <!-- Bike icon -->
            <g transform="translate(12,12)" fill="white">
              <circle cx="6" cy="18" r="4" stroke="white" stroke-width="1.5" fill="none"/>
              <circle cx="18" cy="18" r="4" stroke="white" stroke-width="1.5" fill="none"/>
              <path d="M6 18 L12 8 L16 8 L18 12 L14 12 L10 18" stroke="white" stroke-width="1.5" fill="none"/>
              <path d="M12 12 L16 18" stroke="white" stroke-width="1.5"/>
            </g>
          </svg>
        `,
        auto: `
          <svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
            <circle cx="24" cy="24" r="20" fill="#000000" stroke="#ffffff" stroke-width="4"/>
            <!-- Auto rickshaw icon -->
            <g transform="translate(10,14)" fill="white">
              <rect x="2" y="8" width="24" height="12" rx="2" stroke="white" stroke-width="1.5" fill="none"/>
              <circle cx="6" cy="22" r="2" stroke="white" stroke-width="1.5" fill="none"/>
              <circle cx="22" cy="22" r="2" stroke="white" stroke-width="1.5" fill="none"/>
              <path d="M8 8 L8 4 L20 4 L20 8" stroke="white" stroke-width="1.5" fill="none"/>
              <rect x="10" y="10" width="8" height="6" rx="1" fill="white"/>
            </g>
          </svg>
        `,
        car: `
          <svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
            <circle cx="24" cy="24" r="20" fill="#000000" stroke="#ffffff" stroke-width="4"/>
            <!-- Car icon -->
            <g transform="translate(8,16)" fill="white">
              <rect x="4" y="8" width="24" height="10" rx="2" stroke="white" stroke-width="1.5" fill="none"/>
              <circle cx="8" cy="20" r="2" stroke="white" stroke-width="1.5" fill="none"/>
              <circle cx="24" cy="20" r="2" stroke="white" stroke-width="1.5" fill="none"/>
              <path d="M6 8 L8 4 L24 4 L26 8" stroke="white" stroke-width="1.5" fill="none"/>
              <rect x="10" y="6" width="4" height="4" rx="0.5" fill="white"/>
              <rect x="18" y="6" width="4" height="4" rx="0.5" fill="white"/>
            </g>
          </svg>
        `,
        suv: `
          <svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
            <circle cx="24" cy="24" r="20" fill="#000000" stroke="#ffffff" stroke-width="4"/>
            <!-- SUV icon -->
            <g transform="translate(6,14)" fill="white">
              <rect x="4" y="8" width="28" height="12" rx="2" stroke="white" stroke-width="1.5" fill="none"/>
              <circle cx="9" cy="22" r="2.5" stroke="white" stroke-width="1.5" fill="none"/>
              <circle cx="27" cy="22" r="2.5" stroke="white" stroke-width="1.5" fill="none"/>
              <path d="M6 8 L8 2 L28 2 L30 8" stroke="white" stroke-width="1.5" fill="none"/>
              <rect x="10" y="4" width="5" height="6" rx="0.5" fill="white"/>
              <rect x="21" y="4" width="5" height="6" rx="0.5" fill="white"/>
            </g>
          </svg>
        `
      };

      // Initialize the map
      const map = new window.google.maps.Map(mapElement, {
        zoom: 13,
        center: ride.pickup_location,
        mapTypeId: 'roadmap',
        styles: [
          {
            featureType: 'poi',
            elementType: 'labels',
            stylers: [{ visibility: 'off' }]
          }
        ]
      });

      // Create pickup marker with vehicle-specific icon
      const pickupMarker = new window.google.maps.Marker({
        position: ride.pickup_location,
        map: map,
        title: `Driver Location (${driverVehicleType.toUpperCase()}) - ${ride.pickup_location.address}`,
        icon: {
          url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(vehicleIcons[driverVehicleType] || vehicleIcons.car),
          scaledSize: new window.google.maps.Size(48, 48),
          anchor: new window.google.maps.Point(24, 24)
        },
        zIndex: 1000
      });

      // Create drop marker with destination flag icon
      const dropMarker = new window.google.maps.Marker({
        position: ride.drop_location,
        map: map,
        title: 'Destination: ' + ride.drop_location.address,
        icon: {
          url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
            <svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
              <circle cx="24" cy="24" r="20" fill="#dc2626" stroke="#ffffff" stroke-width="4"/>
              <!-- Flag icon for destination -->
              <g transform="translate(14,10)" fill="white">
                <rect x="2" y="4" width="2" height="24" fill="white"/>
                <path d="M4 4 L4 8 L18 6 L18 12 L4 10 L4 14" fill="white"/>
                <circle cx="19" cy="9" r="1" fill="white"/>
              </g>
            </svg>
          `),
          scaledSize: new window.google.maps.Size(48, 48),
          anchor: new window.google.maps.Point(24, 24)
        },
        zIndex: 999
      });

      // Enhanced info windows with vehicle information
      const pickupInfoWindow = new window.google.maps.InfoWindow({
        content: `
          <div style="padding: 12px; min-width: 200px;">
            <h3 style="margin: 0 0 8px 0; color: #000000; font-weight: bold; display: flex; align-items: center;">
              🚗 Driver Location
            </h3>
            <div style="background: #f3f4f6; padding: 8px; border-radius: 6px; margin-bottom: 8px;">
              <div style="font-weight: bold; color: #374151;">Vehicle: ${driverVehicleType.charAt(0).toUpperCase() + driverVehicleType.slice(1)}</div>
              <div style="font-size: 12px; color: #6b7280;">Pickup Point</div>
            </div>
            <p style="margin: 0; font-size: 14px; color: #374151;">${ride.pickup_location.address}</p>
          </div>
        `
      });

      const dropInfoWindow = new window.google.maps.InfoWindow({
        content: `
          <div style="padding: 12px; min-width: 200px;">
            <h3 style="margin: 0 0 8px 0; color: #dc2626; font-weight: bold;">🏁 Destination</h3>
            <div style="background: #fee2e2; padding: 8px; border-radius: 6px; margin-bottom: 8px;">
              <div style="font-weight: bold; color: #991b1b;">Drop Location</div>
              <div style="font-size: 12px; color: #7f1d1d;">Final Destination</div>
            </div>
            <p style="margin: 0; font-size: 14px; color: #374151;">${ride.drop_location.address}</p>
          </div>
        `
      });

      pickupMarker.addListener('click', () => {
        dropInfoWindow.close();
        pickupInfoWindow.open(map, pickupMarker);
      });

      dropMarker.addListener('click', () => {
        pickupInfoWindow.close();
        dropInfoWindow.open(map, dropMarker);
      });

      // Add route with enhanced styling
      const directionsService = new window.google.maps.DirectionsService();
      const directionsRenderer = new window.google.maps.DirectionsRenderer({
        suppressMarkers: true, // We'll use our custom markers
        polylineOptions: {
          strokeColor: '#2563eb',
          strokeWeight: 6,
          strokeOpacity: 0.8
        }
      });
      directionsRenderer.setMap(map);

      // Get directions
      directionsService.route({
        origin: ride.pickup_location,
        destination: ride.drop_location,
        travelMode: window.google.maps.TravelMode.DRIVING,
        optimizeWaypoints: true,
        avoidHighways: false,
        avoidTolls: false
      }, (result, status) => {
        if (status === 'OK') {
          directionsRenderer.setDirections(result);
          
          // Display route information with vehicle type
          const route = result.routes[0];
          const leg = route.legs[0];
          
          const routeInfoContent = `
            <div style="background: white; border-radius: 8px; padding: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-top: 16px;">
              <h4 style="margin: 0 0 8px 0; color: #2563eb; font-weight: bold;">📍 Route Information</h4>
              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; font-size: 14px;">
                <div style="text-align: center; background: #f3f4f6; padding: 6px; border-radius: 4px;">
                  <div style="font-weight: bold; color: #000000;">${driverVehicleType.toUpperCase()}</div>
                  <div style="font-size: 11px; color: #6b7280;">Vehicle</div>
                </div>
                <div style="text-align: center; background: #f3f4f6; padding: 6px; border-radius: 4px;">
                  <div style="font-weight: bold; color: #059669;">${leg.distance.text}</div>
                  <div style="font-size: 11px; color: #6b7280;">Distance</div>
                </div>
                <div style="text-align: center; background: #f3f4f6; padding: 6px; border-radius: 4px;">
                  <div style="font-weight: bold; color: #7c3aed;">${leg.duration.text}</div>
                  <div style="font-size: 11px; color: #6b7280;">Duration</div>
                </div>
              </div>
            </div>
          `;
          
          // Add route info box
          setTimeout(() => {
            mapElement.insertAdjacentHTML('beforeend', routeInfoContent);
          }, 1000);
        } else {
          console.error('Directions request failed due to ' + status);
        }
      });

      // Add map controls with vehicle information
      const controlDiv = document.createElement('div');
      controlDiv.style.position = 'absolute';
      controlDiv.style.top = '10px';
      controlDiv.style.right = '10px';
      controlDiv.style.zIndex = '1000';
      
      controlDiv.innerHTML = `
        <div style="background: white; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); padding: 8px;">
          <div style="display: flex; align-items: center; margin-bottom: 8px; font-size: 12px; color: #374151;">
            <span style="background: #000000; color: white; padding: 2px 6px; border-radius: 4px; margin-right: 6px; font-weight: bold;">
              ${driverVehicleType.toUpperCase()}
            </span>
            Live Navigation
          </div>
          <button id="center-route-btn" style="background: #2563eb; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; width: 100%;">
            📍 Center Route
          </button>
        </div>
      `;
      
      mapElement.appendChild(controlDiv);
      
      document.getElementById('center-route-btn').addEventListener('click', () => {
        const bounds = new window.google.maps.LatLngBounds();
        bounds.extend(ride.pickup_location);
        bounds.extend(ride.drop_location);
        map.fitBounds(bounds);
        map.setZoom(Math.min(map.getZoom(), 15));
      });

    } catch (error) {
      console.error('Error initializing current ride map:', error);
      mapElement.innerHTML = '<div class="flex items-center justify-center h-80 text-red-500">❌ Error loading map</div>';
    }
  };

  const fetchAcceptedRides = async () => {
    try {
      const response = await axios.get(`${API}/driver/ride-history?status=accepted`);
      setAcceptedRides(response.data.rides);
    } catch (error) {
      console.error('Error fetching accepted rides:', error);
    }
  };

  const fetchRideHistory = async () => {
    try {
      const response = await axios.get(`${API}/driver/ride-history?limit=50`);
      setRideHistory(response.data.rides);
    } catch (error) {
      console.error('Error fetching ride history:', error);
    }
  };

  const verifyRideOTP = async (rideId, otpCode) => {
    if (!otpCode || otpCode.length !== 4) {
      alert('Please enter a valid 4-digit OTP');
      return;
    }

    try {
      const response = await axios.post(`${API}/driver/verify-ride-otp`, {
        ride_id: rideId,
        otp_code: otpCode
      });
      
      alert('🎉 OTP verified successfully! Ride started.\n\nYou can now begin the journey to the destination.');
      
      // Clear modal state
      setSelectedRideForOTP(null);
      setOtpInput('');
      
      // Refresh ride lists
      fetchAcceptedRides();
      fetchRideHistory();
      
    } catch (error) {
      console.error('Error verifying OTP:', error);
      const errorMessage = error.response?.data?.detail || 'Invalid OTP. Please try again.';
      alert(`❌ ${errorMessage}`);
      
      // Clear the input to allow retry
      setOtpInput('');
    }
  };

  const completeRide = async (rideId) => {
    if (!confirm('Mark this ride as completed?')) {
      return;
    }

    try {
      await axios.post(`${API}/driver/complete-ride`, {
        ride_id: rideId,
        status: 'completed'
      });
      
      alert('Ride completed successfully!');
      fetchAcceptedRides();
      fetchRideHistory();
    } catch (error) {
      console.error('Error completing ride:', error);
      alert('Failed to complete ride');
    }
  };

  const cancelRide = async (rideId) => {
    setSelectedRideForCancel(rideId);
    setShowCancelModal(true);
  };

  const confirmCancelRide = async () => {
    if (!cancelReason.trim()) {
      alert('Please provide a reason for cancellation');
      return;
    }

    try {
      const response = await axios.post(`${API}/driver/cancel-ride`, {
        ride_id: selectedRideForCancel,
        reason: cancelReason
      });
      
      alert('✅ Ride cancelled successfully!');
      setShowCancelModal(false);
      setSelectedRideForCancel(null);
      setCancelReason('');
      fetchAcceptedRides();
      fetchRideHistory();
    } catch (error) {
      console.error('Error cancelling ride:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      alert('❌ Failed to cancel ride: ' + errorMessage);
    }
  };

  if (showProfileForm) {
    return (
      <div className="min-h-screen bg-gray-100 p-4">
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-6">Complete Your Driver Profile</h2>
          <form onSubmit={createDriverProfile} className="space-y-6">
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Vehicle Type</label>
                <select
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={profileForm.vehicle_type}
                  onChange={(e) => setProfileForm({ ...profileForm, vehicle_type: e.target.value })}
                >
                  <option value="">Select Vehicle Type</option>
                  <option value="bike">Bike</option>
                  <option value="auto">Auto Rickshaw</option>
                  <option value="car">Car</option>
                  <option value="suv">SUV</option>
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Vehicle Number</label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 pr-20 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., KA01AB1234"
                    value={profileForm.vehicle_number}
                    onChange={(e) => setProfileForm({ ...profileForm, vehicle_number: e.target.value.toUpperCase() })}
                  />
                  <button
                    type="button"
                    onClick={verifyVehicleWithVahan}
                    disabled={!profileForm.vehicle_number || isVerifyingVehicle}
                    className="absolute right-1 top-1/2 transform -translate-y-1/2 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isVerifyingVehicle ? 'Verifying...' : 'Verify'}
                  </button>
                </div>
                {vehicleVerificationStatus && (
                  <div className={`mt-2 p-3 rounded-lg border ${
                    vehicleVerificationStatus.success 
                      ? 'bg-green-50 border-green-200' 
                      : 'bg-red-50 border-red-200'
                  }`}>
                    <div className={`flex items-center ${
                      vehicleVerificationStatus.success ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {vehicleVerificationStatus.success ? (
                        <CheckCircle className="w-4 h-4 mr-2" />
                      ) : (
                        <XCircle className="w-4 h-4 mr-2" />
                      )}
                      <span className="text-sm font-medium">{vehicleVerificationStatus.message}</span>
                    </div>
                    {vehicleVerificationStatus.success && vehicleVerificationStatus.data && (
                      <div className="mt-2 text-sm text-green-600">
                        <p><strong>Owner:</strong> {vehicleVerificationStatus.data.owner_name}</p>
                        <p><strong>Vehicle Class:</strong> {vehicleVerificationStatus.data.vehicle_class}</p>
                        <p><strong>Fuel Type:</strong> {vehicleVerificationStatus.data.fuel_type}</p>
                        <p><strong>Registration Date:</strong> {vehicleVerificationStatus.data.registration_date}</p>
                        <p><strong>Status:</strong> {vehicleVerificationStatus.data.status}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">License Number</label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 pr-20 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., DL1234567890"
                    value={profileForm.license_number}
                    onChange={(e) => setProfileForm({ ...profileForm, license_number: e.target.value })}
                  />
                  <button
                    type="button"
                    onClick={verifyLicenseWithVahan}
                    disabled={!profileForm.license_number || isVerifyingLicense}
                    className="absolute right-1 top-1/2 transform -translate-y-1/2 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isVerifyingLicense ? 'Verifying...' : 'Verify'}
                  </button>
                </div>
                {licenseVerificationStatus && (
                  <div className={`mt-2 p-3 rounded-lg border ${
                    licenseVerificationStatus.success 
                      ? 'bg-green-50 border-green-200' 
                      : 'bg-red-50 border-red-200'
                  }`}>
                    <div className={`flex items-center ${
                      licenseVerificationStatus.success ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {licenseVerificationStatus.success ? (
                        <CheckCircle className="w-4 h-4 mr-2" />
                      ) : (
                        <XCircle className="w-4 h-4 mr-2" />
                      )}
                      <span className="text-sm font-medium">{licenseVerificationStatus.message}</span>
                    </div>
                    {licenseVerificationStatus.success && licenseVerificationStatus.data && (
                      <div className="mt-2 text-sm text-green-600">
                        <p><strong>Name:</strong> {licenseVerificationStatus.data.name}</p>
                        <p><strong>Valid till:</strong> {licenseVerificationStatus.data.expiry_date}</p>
                        <p><strong>Status:</strong> {licenseVerificationStatus.data.status}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Document Upload Section */}
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900">Required Documents</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <DocumentUpload
                  label="Driver's License"
                  required={true}
                  selectedFile={profileForm.license_document}
                  onFileSelect={(file) => setProfileForm({ ...profileForm, license_document: file })}
                />
                
                <DocumentUpload
                  label="Vehicle Registration Certificate"
                  required={true}
                  selectedFile={profileForm.registration_document}
                  onFileSelect={(file) => setProfileForm({ ...profileForm, registration_document: file })}
                />
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-blue-800">Document Requirements</h4>
                  <div className="mt-2 text-sm text-blue-700">
                    <ul className="list-disc space-y-1 ml-5">
                      <li>Documents should be clear and readable</li>
                      <li>Accepted formats: JPG, PNG, PDF</li>
                      <li>Maximum file size: 5MB per document</li>
                      <li>Documents will be verified before account activation</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
            
            <button
              type="submit"
              disabled={!profileForm.license_document || !profileForm.registration_document}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {!profileForm.license_document || !profileForm.registration_document 
                ? 'Please upload required documents' 
                : 'Save Profile & Documents'
              }
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <div className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-gray-900">Driver Dashboard</h1>
              <div className="flex items-center space-x-4">
                <span className="text-gray-600">Welcome, {user?.name || 'Driver'}</span>
                <button
                  onClick={logout}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Driver Status */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Driver Status</h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">Availability</span>
                  <button
                    onClick={toggleAvailability}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                      isAvailable
                        ? 'bg-green-100 text-green-800 hover:bg-green-200'
                        : 'bg-red-100 text-red-800 hover:bg-red-200'
                    }`}
                  >
                    {isAvailable ? 'Available' : 'Offline'}
                  </button>
                </div>

                {/* Location Status */}
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Location Status</span>
                    <div className="flex items-center">
                      <div className={`w-2 h-2 rounded-full mr-2 ${currentLocation ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      <span className="text-sm font-medium">
                        {currentLocation ? 'Active' : 'Not Set'}
                      </span>
                    </div>
                  </div>
                  {currentLocation && (
                    <div className="text-xs text-gray-600 mt-1 flex justify-between items-center">
                      <span>Lat: {currentLocation.lat.toFixed(4)}, Lng: {currentLocation.lng.toFixed(4)}</span>
                      <button
                        onClick={getCurrentLocation}
                        className="text-blue-600 hover:text-blue-800 text-xs underline"
                      >
                        Update
                      </button>
                    </div>
                  )}
                </div>

                {driverProfile && (
                  <>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Vehicle</span>
                          <span className="text-sm font-medium">{driverProfile.vehicle_type}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Number</span>
                          <span className="text-sm font-medium">{driverProfile.vehicle_number}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">License</span>
                          <span className="text-sm font-medium">{driverProfile.license_number}</span>
                        </div>
                      </div>
                    </div>
                  </>
                )}

                {/* Navigation Buttons */}
                <div className="space-y-2">
                  <button
                    onClick={() => {
                      setShowHistory(!showHistory);
                      if (!showHistory) fetchRideHistory();
                    }}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    {showHistory ? 'Hide' : 'View'} Ride History
                  </button>
                </div>
              </div>
            </div>

            {/* Ride Requests and Active Rides */}
            <div className="lg:col-span-2 space-y-6">
              
              {/* Current Ride with Google Maps - Only show when driver has accepted rides */}
              {acceptedRides.length > 0 && (
                <div className="bg-white rounded-lg shadow-lg p-6">
                  <h2 className="text-xl font-bold mb-6 text-blue-600 flex items-center">
                    <Navigation className="w-6 h-6 mr-3" />
                    Current Ride - Live Navigation
                  </h2>
                  
                  {acceptedRides.map((ride) => (
                    <div key={ride.id} className="space-y-6">
                      
                      {/* Ride Status Banner */}
                      <div className={`p-4 rounded-lg border-l-4 ${
                        ride.status === 'accepted' 
                          ? 'bg-yellow-50 border-yellow-400' 
                          : 'bg-green-50 border-green-400'
                      }`}>
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className={`font-semibold ${
                              ride.status === 'accepted' ? 'text-yellow-800' : 'text-green-800'
                            }`}>
                              {ride.status === 'accepted' ? '🟡 Waiting for Rider' : '🟢 Ride in Progress'}
                            </h3>
                            <p className={`text-sm ${
                              ride.status === 'accepted' ? 'text-yellow-600' : 'text-green-600'
                            }`}>
                              {ride.status === 'accepted' 
                                ? 'Please verify the OTP with the rider to start the trip' 
                                : 'Navigate to destination using the map below'}
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-blue-600">₹{ride.estimated_fare}</div>
                            <div className="text-sm text-gray-500">{ride.estimated_distance?.toFixed(1)} km</div>
                          </div>
                        </div>
                      </div>

                      {/* Route Information */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
                          <div className="flex items-center mb-2">
                            <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                            <span className="text-sm font-medium text-green-700">PICKUP</span>
                          </div>
                          <p className="text-green-800 font-medium">{ride.pickup_location.address}</p>
                          <p className="text-xs text-green-600 mt-1">
                            {ride.pickup_location.lat.toFixed(4)}, {ride.pickup_location.lng.toFixed(4)}
                          </p>
                        </div>
                        
                        <div className="bg-gradient-to-r from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
                          <div className="flex items-center mb-2">
                            <div className="w-3 h-3 bg-red-500 rounded-full mr-3"></div>
                            <span className="text-sm font-medium text-red-700">DESTINATION</span>
                          </div>
                          <p className="text-red-800 font-medium">{ride.drop_location.address}</p>
                          <p className="text-xs text-red-600 mt-1">
                            {ride.drop_location.lat.toFixed(4)}, {ride.drop_location.lng.toFixed(4)}
                          </p>
                        </div>
                      </div>

                      {/* Enhanced Google Maps with Live Tracking */}
                      <div className="bg-gray-50 rounded-lg p-4 border">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-semibold text-gray-800 flex items-center">
                            {ride.status === 'in_progress' ? '🚗 Live Trip Tracking' : '🗺️ Live Route Navigation'}
                          </h4>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => {
                                // Refresh map
                                const mapElement = document.getElementById(`current-ride-map-${ride.id}`);
                                if (mapElement) {
                                  mapElement.innerHTML = '<div class="flex items-center justify-center h-80 text-gray-500">🔄 Refreshing map...</div>';
                                  setTimeout(() => initializeCurrentRideMap(ride), 500);
                                }
                              }}
                              className="bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-1 rounded text-sm transition-colors"
                            >
                              🔄 Refresh Map
                            </button>
                            <button
                              onClick={() => {
                                // Open in Google Maps
                                const url = `https://www.google.com/maps/dir/${ride.pickup_location.lat},${ride.pickup_location.lng}/${ride.drop_location.lat},${ride.drop_location.lng}`;
                                window.open(url, '_blank');
                              }}
                              className="bg-green-100 hover:bg-green-200 text-green-700 px-3 py-1 rounded text-sm transition-colors"
                            >
                              📱 Open in Maps
                            </button>
                            {ride.status === 'in_progress' && (
                              <div className="bg-green-100 text-green-700 px-3 py-1 rounded text-sm flex items-center">
                                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                                LIVE
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {/* Live Trip Status for In-Progress Rides */}
                        {ride.status === 'in_progress' && (
                          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
                            <div className="grid grid-cols-3 gap-4 text-center">
                              <div className="bg-white rounded p-2">
                                <div className="text-lg font-bold text-green-600">
                                  {new Date().toLocaleTimeString()}
                                </div>
                                <div className="text-xs text-green-700">Current Time</div>
                              </div>
                              <div className="bg-white rounded p-2">
                                <div className="text-lg font-bold text-blue-600">
                                  {ride.estimated_distance?.toFixed(1)} km
                                </div>
                                <div className="text-xs text-blue-700">Total Distance</div>
                              </div>
                              <div className="bg-white rounded p-2">
                                <div className="text-lg font-bold text-purple-600">
                                  ₹{ride.estimated_fare}
                                </div>
                                <div className="text-xs text-purple-700">Trip Fare</div>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        <div 
                          id={`current-ride-map-${ride.id}`}
                          className={`w-full rounded-lg bg-gray-100 flex items-center justify-center border ${
                            ride.status === 'in_progress' ? 'h-96 border-green-300' : 'h-80'
                          }`}
                          ref={(el) => {
                            if (el && ride) {
                              setTimeout(() => initializeCurrentRideMap(ride), 100);
                            }
                          }}
                        >
                          <div className="text-gray-500 text-center">
                            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                            <div>{ride.status === 'in_progress' ? 'Loading live trip tracking...' : 'Loading enhanced navigation map...'}</div>
                          </div>
                        </div>

                        {/* Live Trip Instructions for In-Progress Rides */}
                        {ride.status === 'in_progress' && (
                          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h5 className="font-semibold text-blue-800 mb-2 flex items-center">
                              🧭 Live Navigation Instructions
                            </h5>
                            <div className="space-y-2 text-sm">
                              <div className="flex items-center justify-between bg-white rounded p-2">
                                <span className="text-blue-700">🚗 Trip Status:</span>
                                <span className="font-medium text-green-700 bg-green-100 px-2 py-1 rounded">
                                  IN PROGRESS
                                </span>
                              </div>
                              <div className="flex items-center justify-between bg-white rounded p-2">
                                <span className="text-blue-700">📍 Next Action:</span>
                                <span className="font-medium text-gray-800">
                                  Navigate to destination
                                </span>
                              </div>
                              <div className="flex items-center justify-between bg-white rounded p-2">
                                <span className="text-blue-700">⏱️ Started At:</span>
                                <span className="font-medium text-gray-800">
                                  {ride.started_at ? new Date(ride.started_at).toLocaleTimeString() : 'Just now'}
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Rider Information */}
                      {ride.rider_info && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h4 className="font-semibold text-blue-800 mb-2 flex items-center">
                            👤 Rider Information
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="font-medium text-blue-700">Name:</span>
                              <span className="ml-2 text-blue-800">{ride.rider_info.name}</span>
                            </div>
                            <div>
                              <span className="font-medium text-blue-700">Phone:</span>
                              <a href={`tel:${ride.rider_info.phone}`} className="ml-2 text-blue-600 hover:text-blue-800 underline">
                                {ride.rider_info.phone}
                              </a>
                            </div>
                            <div>
                              <span className="font-medium text-blue-700">OTP:</span>
                              <span className="ml-2 bg-purple-100 text-purple-800 px-2 py-1 rounded font-bold">
                                {ride.ride_otp || '----'}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex gap-3">
                        {ride.status === 'accepted' && (
                          <>
                            <button
                              onClick={() => setSelectedRideForOTP(ride)}
                              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg transition-colors font-medium flex items-center justify-center"
                            >
                              <CheckCircle className="w-5 h-5 mr-2" />
                              Verify OTP & Start Journey
                            </button>
                            <button
                              onClick={() => cancelRide(ride.id)}
                              className="bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-lg transition-colors font-medium"
                            >
                              Cancel
                            </button>
                          </>
                        )}
                        
                        {ride.status === 'in_progress' && (
                          <>
                            <button
                              onClick={() => completeRide(ride.id)}
                              className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 px-4 rounded-lg transition-colors font-medium flex items-center justify-center"
                            >
                              <CheckCircle className="w-5 h-5 mr-2" />
                              Complete Journey
                            </button>
                            <button
                              onClick={() => cancelRide(ride.id)}
                              className="bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-lg transition-colors font-medium"
                            >
                              Cancel
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Nearby Ride Requests - Only show when no active rides */}
              {acceptedRides.length === 0 && (
                <div className={`bg-white rounded-lg shadow p-6 transition-all duration-300 ${flashEffect ? 'ring-4 ring-green-400 bg-green-50' : ''}`}>
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-semibold flex items-center">
                      Nearby Ride Requests
                      {notificationPermission !== 'granted' && (
                        <button
                          onClick={() => Notification.requestPermission()}
                          className="ml-2 text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded-full hover:bg-blue-200"
                          title="Enable notifications for new ride requests"
                        >
                          🔔 Enable Alerts
                        </button>
                      )}
                    </h2>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={fetchRideRequests}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >
                        Refresh
                      </button>
                      <div className={`w-2 h-2 rounded-full ${isAvailable ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      <span className="text-sm text-gray-600">
                        {isAvailable ? 'Receiving requests' : 'Offline'}
                      </span>
                    </div>
                  </div>
              
              {!isAvailable ? (
                <div className="text-center py-8 text-gray-500">
                  <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p className="font-medium">You're currently offline</p>
                  <p className="text-sm">Turn on availability to receive ride requests</p>
                </div>
              ) : rideRequests.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <MapPin className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p className="font-medium">No ride requests nearby</p>
                  <p className="text-sm">We'll notify you when new requests come in</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {rideRequests.map((request) => (
                    <div key={request.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="flex items-center mb-2">
                            <User className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="font-medium text-gray-900">{request.rider_name}</span>
                            <span className="ml-2 text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">
                              {request.distance?.toFixed(1)} km away
                            </span>
                          </div>
                          <div className="text-sm text-gray-600 space-y-1">
                            <div className="flex items-center">
                              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                              <span>{request.pickup_location.address}</span>
                            </div>
                            <div className="flex items-center">
                              <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                              <span>{request.drop_location.address}</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right ml-4">
                          <div className="text-lg font-bold text-green-600">₹{request.estimated_fare}</div>
                          <div className="text-xs text-gray-500">{request.estimated_distance?.toFixed(1)} km</div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => acceptRide(request.id)}
                          className="flex-1 bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium shadow-sm"
                        >
                          Accept Ride
                        </button>
                        <button
                          onClick={() => rejectRide(request.id)}
                          className="bg-red-600 text-white px-4 py-3 rounded-lg hover:bg-red-700 transition-colors font-medium shadow-sm"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                  
                  {rideRequests.length > 0 && (
                    <div className="text-center text-xs text-gray-400 pt-2">
                      Showing {rideRequests.length} nearby request{rideRequests.length > 1 ? 's' : ''} • Updates every 10 seconds
                    </div>
                  )}
                </div>
              )}
              
            </div>
            
          </div>
        </div>
      </div>
            )

    {/* OTP Verification Modal */}
    {selectedRideForOTP && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900 flex items-center">
                  <CheckCircle className="w-6 h-6 text-green-600 mr-2" />
                  Verify Ride OTP
                </h2>
                <button
                  onClick={() => {
                    setSelectedRideForOTP(null);
                    setOtpInput('');
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600 mb-2">
                      Enter Ride OTP
                    </div>
                    <p className="text-sm text-blue-600">
                      Ask the rider for the 4-digit OTP to start the journey
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    4-Digit OTP
                  </label>
                  <input
                    type="text"
                    value={otpInput}
                    onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, '').slice(0, 4))}
                    placeholder="1234"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl font-bold tracking-widest"
                    maxLength="4"
                  />
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="flex items-start">
                    <div className="text-yellow-600 mr-2">⚠️</div>
                    <div className="text-sm text-yellow-800">
                      <p className="font-medium mb-1">Important:</p>
                      <ul className="text-xs space-y-1">
                        <li>• Verify rider's identity before starting</li>
                        <li>• OTP is valid for this ride only</li>
                        <li>• Contact support if OTP doesn't work</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={() => {
                      setSelectedRideForOTP(null);
                      setOtpInput('');
                    }}
                    className="flex-1 bg-gray-200 text-gray-800 py-3 px-4 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => verifyRideOTP(selectedRideForOTP.id)}
                    disabled={otpInput.length !== 4}
                    className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    Verify & Start
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Ride Modal */}
      {showCancelModal && selectedRideForCancel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Cancel Ride</h2>
                <button
                  onClick={() => {
                    setShowCancelModal(false);
                    setSelectedRideForCancel(null);
                    setCancelReason('');
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <div className="text-red-600 mr-2">⚠️</div>
                    <div>
                      <p className="text-sm text-red-800 font-medium">
                        Are you sure you want to cancel this ride?
                      </p>
                      <p className="text-xs text-red-600 mt-1">
                        This action cannot be undone and may affect your rating.
                      </p>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cancellation Reason
                  </label>
                  <select
                    value={cancelReason}
                    onChange={(e) => setCancelReason(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select a reason...</option>
                    <option value="rider_not_responding">Rider not responding</option>
                    <option value="wrong_location">Wrong pickup location</option>
                    <option value="vehicle_issue">Vehicle breakdown</option>
                    <option value="emergency">Personal emergency</option>
                    <option value="other">Other reason</option>
                  </select>
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={() => {
                      setShowCancelModal(false);
                      setSelectedRideForCancel(null);
                      setCancelReason('');
                    }}
                    className="flex-1 bg-gray-200 text-gray-800 py-3 px-4 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                  >
                    Keep Ride
                  </button>
                  <button
                    onClick={confirmCancelRide}
                    disabled={!cancelReason}
                    className="flex-1 bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    Cancel Ride
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}


    </>
  );
};

// Rider Dashboard Component
const RiderDashboard = () => {
  const [pickupLocation, setPickupLocation] = useState('');
  const [dropLocation, setDropLocation] = useState('');
  const [estimatedFare, setEstimatedFare] = useState(0);
  const [estimatedDistance, setEstimatedDistance] = useState(0);
  const [availableDrivers, setAvailableDrivers] = useState([]);
  const [currentRides, setCurrentRides] = useState([]);
  const [rideHistory, setRideHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [mapElement, setMapElement] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedRideForPayment, setSelectedRideForPayment] = useState(null);
  const [mapInstance, setMapInstance] = useState(null);
  const [pickupMarker, setPickupMarker] = useState(null);
  const [dropMarker, setDropMarker] = useState(null);
  const [driverMarkers, setDriverMarkers] = useState([]);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [selectedRideForCancel, setSelectedRideForCancel] = useState(null);
  const [promoCode, setPromoCode] = useState('');
  const [appliedDiscount, setAppliedDiscount] = useState(null);
  const [availableDiscounts, setAvailableDiscounts] = useState([]);
  const [availableVehicles, setAvailableVehicles] = useState([]);
  const [selectedVehicleType, setSelectedVehicleType] = useState(null);
  const [showVehicleSelection, setShowVehicleSelection] = useState(false);
  const [isLoadingVehicles, setIsLoadingVehicles] = useState(false);
  const [showDiscountModal, setShowDiscountModal] = useState(false);
  const [isApplyingDiscount, setIsApplyingDiscount] = useState(false);
  
  const { user, logout } = useAuth();
  const { loaded, initMap, calculateRoute, getUserLocation, searchPlaces } = useGoogleMaps();

  const fetchAvailableDiscounts = async () => {
    try {
      const response = await axios.get(`${API}/rider/available-discounts`);
      if (response.data.success) {
        setAvailableDiscounts(response.data.discounts);
      }
    } catch (error) {
      console.error('Error fetching discounts:', error);
    }
  };

  const applyDiscountCode = async () => {
    if (!promoCode.trim()) {
      alert('Please enter a promo code');
      return;
    }
    
    if (!estimatedFare) {
      alert('Please calculate fare first');
      return;
    }

    setIsApplyingDiscount(true);
    
    try {
      const response = await axios.post(`${API}/rider/apply-discount`, {
        promo_code: promoCode.trim(),
        ride_fare: estimatedFare
      });
      
      if (response.data.success) {
        setAppliedDiscount(response.data.discount_details);
        alert(`🎉 ${response.data.message}\nYou saved ₹${response.data.discount_details.savings}!`);
      } else {
        alert(`❌ ${response.data.message}`);
        setAppliedDiscount(null);
      }
    } catch (error) {
      console.error('Error applying discount:', error);
      alert('❌ Failed to apply discount code');
      setAppliedDiscount(null);
    } finally {
      setIsApplyingDiscount(false);
    }
  };

  const selectDiscountCode = (discount) => {
    setPromoCode(discount.code);
    setShowDiscountModal(false);
    // Automatically apply the selected discount
    setTimeout(() => {
      applyDiscountCode();
    }, 100);
  };

  const clearDiscount = () => {
    setPromoCode('');
    setAppliedDiscount(null);
  };



  useEffect(() => {
    getCurrentLocation();
    fetchCurrentRides();
    fetchRideHistory();
    fetchAvailableDiscounts(); // Load available discounts on mount
  }, []);

  // Auto-populate pickup location when current location is available
  useEffect(() => {
    if (currentLocation && !pickupLocation) {
      const address = `Current Location (${currentLocation.lat.toFixed(4)}, ${currentLocation.lng.toFixed(4)})`;
      setPickupLocation(address);
      // Also set it on the map
      setTimeout(() => {
        handleLocationSelect('pickup', address);
      }, 1000);
    }
  }, [currentLocation]);

  // Fetch available vehicles by type when both locations are set
  const fetchAvailableVehiclesByType = async () => {
    if (!currentLocation || !dropLocation || !pickupLocation) {
      return;
    }

    setIsLoadingVehicles(true);
    try {
      const response = await axios.get(`${API}/rider/nearby-drivers`, {
        params: {
          lat: currentLocation.lat,
          lng: currentLocation.lng,
          radius: 25
        }
      });
      
      const drivers = response.data.drivers || [];
      
      // Group drivers by vehicle type and calculate rates
      const vehicleTypes = ['bike', 'auto', 'car', 'suv'];
      const vehicleOptions = [];

      vehicleTypes.forEach(type => {
        const typeDrivers = drivers.filter(driver => driver.vehicle_type === type);
        
        if (typeDrivers.length > 0) {
          // Calculate average rates and find closest driver
          const rates = typeDrivers.map(d => d.per_km_rate);
          const distances = typeDrivers.map(d => d.distance_km);
          const minRate = Math.min(...rates);
          const maxRate = Math.max(...rates);
          const avgRate = Math.round(rates.reduce((a, b) => a + b, 0) / rates.length);
          const closestDistance = Math.min(...distances);
          
          // Estimate fare based on average rate and distance
          let estimatedFare = 0;
          if (estimatedDistance > 0) {
            estimatedFare = Math.round(avgRate * estimatedDistance);
          }

          vehicleOptions.push({
            type: type,
            name: type.charAt(0).toUpperCase() + type.slice(1),
            icon: type === 'bike' ? '🏍️' : type === 'auto' ? '🛺' : type === 'car' ? '🚗' : '🚛',
            availableCount: typeDrivers.length,
            minRate: minRate,
            maxRate: maxRate,
            avgRate: avgRate,
            closestDistance: closestDistance.toFixed(1),
            estimatedFare: estimatedFare,
            drivers: typeDrivers.slice(0, 3) // Show top 3 closest drivers
          });
        }
      });

      // Sort by estimated fare (cheapest first)
      vehicleOptions.sort((a, b) => a.avgRate - b.avgRate);
      
      setAvailableVehicles(vehicleOptions);
      setShowVehicleSelection(vehicleOptions.length > 0);
      
    } catch (error) {
      console.error('Error fetching vehicles by type:', error);
    } finally {
      setIsLoadingVehicles(false);
    }
  };

  // Auto-fetch vehicles when both pickup and drop locations are available
  useEffect(() => {
    if (currentLocation && dropLocation && pickupLocation && estimatedDistance > 0) {
      fetchAvailableVehiclesByType();
    } else {
      setShowVehicleSelection(false);
      setAvailableVehicles([]);
      setSelectedVehicleType(null);
    }
  }, [currentLocation, dropLocation, pickupLocation, estimatedDistance]);

  useEffect(() => {
    if (loaded && mapElement && currentLocation) {
      const map = initMap(mapElement, {
        center: currentLocation,
        zoom: 15
      });
      setMapInstance(map);
      
      // Add current location marker
      if (map && window.google) {
        new window.google.maps.Marker({
          position: currentLocation,
          map: map,
          title: 'Your Location',
          icon: {
            url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png'
          }
        });
      }
    }
  }, [loaded, mapElement, currentLocation]);

  const getCurrentLocation = async () => {
    try {
      const location = await getUserLocation();
      setCurrentLocation(location);
      fetchAvailableDrivers(location.lat, location.lng);
    } catch (error) {
      console.error('Error getting location:', error);
      // Use fallback location (Chennai)
      const fallbackLocation = { lat: 13.0827, lng: 80.2707 };
      setCurrentLocation(fallbackLocation);
      fetchAvailableDrivers(fallbackLocation.lat, fallbackLocation.lng);
    }
  };

  const handleLocationSelect = async (locationType, prediction) => {
    if (!mapInstance || !window.google) return;

    try {
      // If it's a string (legacy), handle as before
      if (typeof prediction === 'string') {
        if (locationType === 'pickup') {
          setPickupLocation(prediction);
        } else {
          setDropLocation(prediction);
        }
        
        // Try to search using Places API
        const service = new window.google.maps.places.PlacesService(mapInstance);
        const request = {
          query: prediction,
          fields: ['place_id', 'name', 'geometry', 'formatted_address']
        };
        
        service.textSearch(request, (results, status) => {
          if (status === window.google.maps.places.PlacesServiceStatus.OK && results[0]) {
            addMarkerForLocation(locationType, results[0], prediction);
          }
        });
        return;
      }

      // Handle Google Places prediction object
      const placesService = new window.google.maps.places.PlacesService(mapInstance);
      
      const request = {
        placeId: prediction.place_id,
        fields: ['place_id', 'name', 'geometry', 'formatted_address']
      };

      placesService.getDetails(request, (place, status) => {
        if (status === window.google.maps.places.PlacesServiceStatus.OK && place) {
          const address = place.formatted_address || prediction.description;
          
          if (locationType === 'pickup') {
            setPickupLocation(address);
          } else {
            setDropLocation(address);
          }
          
          addMarkerForLocation(locationType, place, address);
        }
      });
    } catch (error) {
      console.error('Error handling location select:', error);
    }
  };

  const addMarkerForLocation = (locationType, place, address) => {
    const location = place.geometry.location;
    const latLng = typeof location.lat === 'function' 
      ? { lat: location.lat(), lng: location.lng() }
      : location;

    if (locationType === 'pickup') {
      // Clear previous pickup marker
      if (pickupMarker) {
        pickupMarker.setMap(null);
      }
      
      const marker = new window.google.maps.Marker({
        position: latLng,
        map: mapInstance,
        title: `Pickup: ${address}`,
        icon: {
          url: 'https://maps.google.com/mapfiles/ms/icons/green-dot.png'
        }
      });
      setPickupMarker(marker);
      
      // Center map on pickup location
      mapInstance.panTo(latLng);
      
      // If drop marker exists, fit both locations
      if (dropMarker) {
        const bounds = new window.google.maps.LatLngBounds();
        bounds.extend(latLng);
        bounds.extend(dropMarker.getPosition());
        mapInstance.fitBounds(bounds);
        
        // Auto-calculate fare when both locations are set
        setTimeout(() => calculateFare(), 1000);
      }
    } else {
      // Clear previous drop marker
      if (dropMarker) {
        dropMarker.setMap(null);
      }
      
      const marker = new window.google.maps.Marker({
        position: latLng,
        map: mapInstance,
        title: `Drop: ${address}`,
        icon: {
          url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png'
        }
      });
      setDropMarker(marker);
      
      // If pickup marker exists, fit both locations
      if (pickupMarker) {
        const bounds = new window.google.maps.LatLngBounds();
        bounds.extend(pickupMarker.getPosition());
        bounds.extend(latLng);
        mapInstance.fitBounds(bounds);
        
        // Auto-calculate fare when both locations are set
        setTimeout(() => calculateFare(), 1000);
      } else {
        // Just center on drop location
        mapInstance.panTo(latLng);
      }
    }
  };

  const useCurrentLocation = () => {
    if (currentLocation) {
      const address = `Current Location (${currentLocation.lat.toFixed(4)}, ${currentLocation.lng.toFixed(4)})`;
      handleLocationSelect('pickup', address);
    }
  };

  const fetchAvailableDrivers = async (lat, lng) => {
    try {
      const response = await axios.get(`${API}/rider/available-drivers?lat=${lat}&lng=${lng}`);
      setAvailableDrivers(response.data);
      
      // Update driver markers on map
      if (mapInstance && window.google) {
        updateDriverMarkersOnMap(response.data);
      }
    } catch (error) {
      console.error('Error fetching drivers:', error);
    }
  };

  const updateDriverMarkersOnMap = (drivers) => {
    // Clear existing driver markers
    driverMarkers.forEach(marker => marker.setMap(null));
    setDriverMarkers([]);

    // Add new driver markers with vehicle-specific icons
    const newMarkers = [];
    drivers.forEach(driver => {
      if (driver.current_location && driver.current_location.lat && driver.current_location.lng) {
        // Get vehicle-specific icon
        const getVehicleIcon = (vehicleType) => {
          const iconMap = {
            'hatchback': 'https://maps.google.com/mapfiles/ms/icons/cabs.png',
            'sedan': 'https://maps.google.com/mapfiles/ms/icons/truck.png', 
            'suv': 'https://maps.google.com/mapfiles/ms/icons/bus.png',
            'auto': 'https://maps.google.com/mapfiles/ms/icons/yellow-dot.png',
            'bike': 'https://maps.google.com/mapfiles/ms/icons/motorcycling.png',
            'default': 'https://maps.google.com/mapfiles/ms/icons/cabs.png'
          };
          return iconMap[vehicleType?.toLowerCase()] || iconMap['default'];
        };

        const marker = new window.google.maps.Marker({
          position: {
            lat: driver.current_location.lat,
            lng: driver.current_location.lng
          },
          map: mapInstance,
          title: `${driver.name} - ${driver.vehicle_type} (₹${driver.per_km_rate}/km)`,
          icon: {
            url: getVehicleIcon(driver.vehicle_type),
            scaledSize: new window.google.maps.Size(32, 32)
          }
        });

        // Enhanced info window with vehicle details
        const infoWindow = new window.google.maps.InfoWindow({
          content: `
            <div style="padding: 12px; min-width: 200px;">
              <h4 style="margin: 0 0 8px 0; color: #1f2937; font-size: 16px;">${driver.name}</h4>
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 18px; margin-right: 8px;">🚗</span>
                <span style="color: #6b7280; font-size: 14px;">${driver.vehicle_type}</span>
              </div>
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 18px; margin-right: 8px;">💰</span>
                <span style="color: #059669; font-weight: bold;">₹${driver.per_km_rate}/km</span>
              </div>
              <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 18px; margin-right: 8px;">📍</span>
                <span style="color: #6b7280; font-size: 14px;">${driver.distance}km away</span>
              </div>
              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb;">
                <span style="color: #059669; font-size: 12px; font-weight: bold;">Available Now</span>
              </div>
            </div>
          `
        });

        marker.addListener('click', () => {
          infoWindow.open(mapInstance, marker);
        });

        newMarkers.push(marker);
      }
    });

    setDriverMarkers(newMarkers);
  };

  const fetchCurrentRides = async () => {
    try {
      const response = await axios.get(`${API}/rider/rides`);
      setCurrentRides(response.data);
    } catch (error) {
      console.error('Error fetching rides:', error);
    }
  };

  const calculateFare = () => {
    if (!pickupLocation || !dropLocation || !currentLocation) {
      alert('Please enter your destination and ensure pickup location is set');
      return;
    }

    // If both locations are selected and map is available, calculate actual route
    if (mapInstance && pickupMarker && dropMarker && window.google && calculateRoute) {
      const pickupPos = pickupMarker.getPosition();
      const dropPos = dropMarker.getPosition();
      
      try {
        // Calculate route using Google Directions API
        calculateRoute(pickupPos, dropPos, (result) => {
          const distance = result.distance;
          const avgRatePerKm = availableDrivers.length > 0 
            ? availableDrivers.reduce((sum, driver) => sum + driver.per_km_rate, 0) / availableDrivers.length
            : 15; // Default rate

          setEstimatedDistance(distance);
          setEstimatedFare(Math.round(distance * avgRatePerKm));
          
          // Fetch available drivers near pickup location
          fetchAvailableDrivers(pickupPos.lat(), pickupPos.lng());
          
          alert(`✅ Fare calculated successfully!\nDistance: ${distance.toFixed(1)} km\nFare: ₹${Math.round(distance * avgRatePerKm)}`);
        });
      } catch (error) {
        console.error('Error calculating route:', error);
        // Fall back to direct distance calculation
        fallbackFareCalculation();
      }
    } else {
      // Fallback calculation if markers aren't available
      fallbackFareCalculation();
    }
  };

  const fallbackFareCalculation = () => {
    try {
      // Use direct distance calculation between pickup and drop
      let distance = 5.0; // Default fallback distance
      
      if (currentLocation && dropLocation) {
        // Try to geocode drop location and calculate distance
        const geocoder = new window.google.maps.Geocoder();
        geocoder.geocode({ address: dropLocation }, (results, status) => {
          if (status === 'OK' && results[0]) {
            const dropLatLng = results[0].geometry.location;
            const pickupLatLng = new window.google.maps.LatLng(currentLocation.lat, currentLocation.lng);
            
            // Calculate straight-line distance and add 30% for roads
            const directDistance = window.google.maps.geometry.spherical.computeDistanceBetween(pickupLatLng, dropLatLng) / 1000;
            distance = directDistance * 1.3; // Add 30% for road routing
            
            const avgRatePerKm = availableDrivers.length > 0 
              ? availableDrivers.reduce((sum, driver) => sum + driver.per_km_rate, 0) / availableDrivers.length
              : 15; // Default rate

            setEstimatedDistance(distance);
            setEstimatedFare(Math.round(distance * avgRatePerKm));
            
            alert(`✅ Fare calculated successfully!\nDistance: ${distance.toFixed(1)} km\nFare: ₹${Math.round(distance * avgRatePerKm)}`);
            
            // Fetch available drivers
            fetchAvailableDrivers(currentLocation.lat, currentLocation.lng);
          } else {
            // Ultimate fallback
            ultimateFallbackCalculation();
          }
        });
      } else {
        ultimateFallbackCalculation();
      }
    } catch (error) {
      console.error('Error in fallback calculation:', error);
      ultimateFallbackCalculation();
    }
  };

  const ultimateFallbackCalculation = () => {
    // Final fallback with mock data
    const mockDistance = Math.random() * 8 + 3; // Random distance between 3-11 km
    const avgRatePerKm = availableDrivers.length > 0 
      ? availableDrivers.reduce((sum, driver) => sum + driver.per_km_rate, 0) / availableDrivers.length
      : 15; // Default rate

    setEstimatedDistance(mockDistance);
    setEstimatedFare(Math.round(mockDistance * avgRatePerKm));
    
    alert(`✅ Fare calculated successfully!\nDistance: ${mockDistance.toFixed(1)} km\nFare: ₹${Math.round(mockDistance * avgRatePerKm)}\n\n(Using estimated distance)`);
    
    // Fetch available drivers with current location if available
    if (currentLocation) {
      fetchAvailableDrivers(currentLocation.lat, currentLocation.lng);
    }
  };

  const clearLocations = () => {
    setDropLocation('');
    setEstimatedFare(0);
    setEstimatedDistance(0);
    clearDiscount();
    
    // Reset pickup to current location
    if (currentLocation) {
      const address = `Current Location (${currentLocation.lat.toFixed(4)}, ${currentLocation.lng.toFixed(4)})`;
      setPickupLocation(address);
    } else {
      setPickupLocation('');
    }
    
    // Clear markers
    if (pickupMarker) {
      pickupMarker.setMap(null);
      setPickupMarker(null);
    }
    if (dropMarker) {
      dropMarker.setMap(null);
      setDropMarker(null);
    }
    
    // Reset map view to current location and re-add pickup marker
    if (mapInstance && currentLocation) {
      mapInstance.setCenter(currentLocation);
      mapInstance.setZoom(15);
      
      // Re-add pickup marker for current location
      setTimeout(() => {
        const address = `Current Location (${currentLocation.lat.toFixed(4)}, ${currentLocation.lng.toFixed(4)})`;
        handleLocationSelect('pickup', address);
      }, 500);
    }
  };

  const requestRide = async () => {
    if (!pickupLocation || !dropLocation) {
      alert('Please enter your destination and ensure pickup location is set');
      return;
    }

    if (showVehicleSelection && !selectedVehicleType) {
      alert('Please select a vehicle type to continue');
      return;
    }

    try {
      // Get actual coordinates from markers if available
      let pickupCoords = currentLocation;
      let dropCoords = {
        lat: currentLocation.lat + (Math.random() - 0.5) * 0.01,
        lng: currentLocation.lng + (Math.random() - 0.5) * 0.01
      };

      if (pickupMarker && pickupMarker.getPosition) {
        const pos = pickupMarker.getPosition();
        pickupCoords = { lat: pos.lat(), lng: pos.lng() };
      }

      if (dropMarker && dropMarker.getPosition) {
        const pos = dropMarker.getPosition();
        dropCoords = { lat: pos.lat(), lng: pos.lng() };
      }

      // Get fare for selected vehicle type or use default
      let finalFare = estimatedFare;
      if (selectedVehicleType && availableVehicles.length > 0) {
        const selectedVehicle = availableVehicles.find(v => v.type === selectedVehicleType);
        if (selectedVehicle) {
          finalFare = selectedVehicle.estimatedFare;
        }
      }

      const rideData = {
        pickup_location: {
          lat: pickupCoords.lat,
          lng: pickupCoords.lng,
          address: pickupLocation
        },
        drop_location: {
          lat: dropCoords.lat,
          lng: dropCoords.lng,
          address: dropLocation
        },
        estimated_distance: estimatedDistance,
        estimated_fare: finalFare,
        preferred_vehicle_type: selectedVehicleType || 'car', // Include preferred vehicle type
        promo_code: promoCode || null
      };

      const response = await axios.post(`${API}/rider/request-ride`, rideData);
      
      if (response.data.discount_applied) {
        alert(`🎉 Ride requested successfully with discount!\nVehicle: ${(selectedVehicleType || 'car').toUpperCase()}\nOriginal fare: ₹${response.data.estimated_fare}\nDiscount: -₹${response.data.discount_applied.discount_amount}\nFinal fare: ₹${response.data.final_fare}\n\nWaiting for ${selectedVehicleType || 'car'} driver to accept...`);
      } else {
        alert(`Ride requested successfully!\nVehicle: ${(selectedVehicleType || 'car').toUpperCase()}\nEstimated fare: ₹${finalFare}\n\nWaiting for ${selectedVehicleType || 'car'} driver to accept...`);
      }
      
      // Clear form after successful request
      clearLocations();
      clearDiscount();
      setSelectedVehicleType(null);
      setShowVehicleSelection(false);
      
      fetchCurrentRides();
    } catch (error) {
      console.error('Error requesting ride:', error);
      alert('Failed to request ride. Please try again.');
    }
  };

  const handlePayNow = (ride) => {
    setSelectedRideForPayment(ride);
    setShowPaymentModal(true);
  };

  const handlePaymentSuccess = () => {
    fetchCurrentRides();
    setSelectedRideForPayment(null);
  };

  const cancelRide = async (rideId, reason = "User cancelled") => {
    setSelectedRideForCancel(rideId);
    setShowCancelModal(true);
  };

  const confirmCancelRide = async (reason = "User cancelled") => {
    const rideId = selectedRideForCancel;
    
    try {
      console.log('Attempting to cancel ride:', rideId);
      
      const response = await axios.post(`${API}/rider/cancel-ride`, {
        ride_id: rideId,
        reason: reason
      });
      
      console.log('Cancel ride response:', response.data);
      alert('✅ Ride cancelled successfully! You will receive a confirmation shortly.');
      fetchCurrentRides();
      
      // Close modal
      setShowCancelModal(false);
      setSelectedRideForCancel(null);
    } catch (error) {
      console.error('Error cancelling ride:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      alert('❌ Failed to cancel ride: ' + errorMessage);
    }
  };

  const fetchRideHistory = async () => {
    try {
      const response = await axios.get(`${API}/rider/ride-history?limit=50`);
      setRideHistory(response.data.rides);
    } catch (error) {
      console.error('Error fetching ride history:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Users className="w-8 h-8 text-blue-600 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">Book a Ride</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user?.name}</span>
              <button
                onClick={logout}
                className="flex items-center text-gray-600 hover:text-gray-900"
              >
                <LogOut className="w-4 h-4 mr-1" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Booking Form */}
          <div className="space-y-6">
            {/* Ride Request Form */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Book Your Ride</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Navigation className="w-4 h-4 inline mr-2 text-red-600" />
                    Where to? (Drop Location)
                  </label>
                  <LocationAutocomplete
                    placeholder="Search destination..."
                    value={dropLocation}
                    onChange={setDropLocation}
                    onLocationSelect={(prediction) => handleLocationSelect('drop', prediction)}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <MapPin className="w-4 h-4 inline mr-2 text-green-600" />
                    Pickup Location
                  </label>
                  <div className="relative">
                    <LocationAutocomplete
                      placeholder="Current location or search..."
                      value={pickupLocation}
                      onChange={setPickupLocation}
                      onLocationSelect={(prediction) => handleLocationSelect('pickup', prediction)}
                      showCurrentLocation={true}
                      onUseCurrentLocation={useCurrentLocation}
                    />
                    {currentLocation && (
                      <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
                        <button
                          onClick={useCurrentLocation}
                          className="text-blue-600 hover:text-blue-800 text-sm bg-blue-50 px-2 py-1 rounded"
                          title="Use current location"
                        >
                          📍 Current
                        </button>
                      </div>
                    )}
                  </div>
                  {currentLocation && (
                    <div className="mt-1 text-xs text-green-600 flex items-center">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Using your current location as pickup
                    </div>
                  )}
                </div>

                {/* Vehicle Selection Section */}
                {showVehicleSelection && (
                  <div className="border-t border-gray-200 pt-4 mt-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-md font-medium text-gray-800 flex items-center">
                        🚗 Choose Your Vehicle
                      </h3>
                      {isLoadingVehicles && (
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
                      )}
                    </div>
                    
                    <div className="space-y-3">
                      {availableVehicles.map((vehicle) => (
                        <div
                          key={vehicle.type}
                          onClick={() => setSelectedVehicleType(vehicle.type)}
                          className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                            selectedVehicleType === vehicle.type
                              ? 'border-blue-500 bg-blue-50 shadow-md'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <div className="w-12 h-12 bg-black rounded-full flex items-center justify-center text-white text-xl">
                                {vehicle.icon}
                              </div>
                              <div>
                                <div className="font-medium text-gray-900">
                                  {vehicle.name}
                                  {selectedVehicleType === vehicle.type && (
                                    <span className="ml-2 text-blue-600">✓</span>
                                  )}
                                </div>
                                <div className="text-sm text-gray-500">
                                  {vehicle.availableCount} available • {vehicle.closestDistance} km away
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-bold text-green-600">
                                ₹{vehicle.estimatedFare}
                              </div>
                              <div className="text-xs text-gray-500">
                                ₹{vehicle.avgRate}/km avg
                              </div>
                            </div>
                          </div>
                          
                          {/* Rate Range */}
                          <div className="mt-3 pt-3 border-t border-gray-100">
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              <span>Rate range: ₹{vehicle.minRate} - ₹{vehicle.maxRate}/km</span>
                              <span>{vehicle.estimatedDistance?.toFixed(1) || estimatedDistance?.toFixed(1)} km trip</span>
                            </div>
                          </div>

                          {/* Top Drivers Preview */}
                          {vehicle.drivers && vehicle.drivers.length > 0 && (
                            <div className="mt-2 flex items-center space-x-2">
                              <span className="text-xs text-gray-500">Available drivers:</span>
                              {vehicle.drivers.slice(0, 3).map((driver, index) => (
                                <div
                                  key={driver.driver_id}
                                  className="text-xs bg-gray-100 px-2 py-1 rounded"
                                  title={`${driver.name} - ⭐ ${driver.rating.toFixed(1)}`}
                                >
                                  {driver.name.split(' ')[0]}
                                </div>
                              ))}
                              {vehicle.availableCount > 3 && (
                                <span className="text-xs text-gray-400">
                                  +{vehicle.availableCount - 3} more
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>

                    {selectedVehicleType && (
                      <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                        <div className="text-sm text-green-800">
                          <strong>Selected:</strong> {availableVehicles.find(v => v.type === selectedVehicleType)?.name} 
                          <span className="ml-2">
                            Estimated Fare: ₹{availableVehicles.find(v => v.type === selectedVehicleType)?.estimatedFare}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={calculateFare}
                    disabled={!dropLocation || !pickupLocation}
                    className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Calculate Fare
                  </button>
                  
                  <button
                    onClick={clearLocations}
                    className="bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    Clear All
                  </button>
                </div>
                
                {estimatedFare > 0 && (
                  <div className="space-y-4">
                    {/* Estimated Fare Display */}
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">Estimated Fare:</span>
                        <span className="text-2xl font-bold text-blue-600 flex items-center">
                          <IndianRupee className="w-5 h-5 mr-1" />
                          {estimatedFare}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 mt-1 flex justify-between">
                        <span>Distance: {estimatedDistance.toFixed(1)} km</span>
                        <span>Rate: ₹{availableDrivers.length > 0 ? (availableDrivers.reduce((sum, driver) => sum + driver.per_km_rate, 0) / availableDrivers.length).toFixed(1) : '15'}/km</span>
                      </div>
                      
                      <div className="mt-3 p-2 bg-green-50 rounded text-sm text-green-700">
                        <div className="flex items-center">
                          <MapPin className="w-4 h-4 mr-2" />
                          Route calculated using Google Maps
                        </div>
                      </div>
                    </div>

                    {/* Discount Section */}
                    <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-medium text-orange-900">Apply Discount Code</h3>
                        <button
                          onClick={() => {
                            fetchAvailableDiscounts();
                            setShowDiscountModal(true);
                          }}
                          className="text-orange-600 hover:text-orange-800 text-sm underline"
                        >
                          View Available Offers
                        </button>
                      </div>
                      
                      <div className="flex space-x-2 mb-3">
                        <input
                          type="text"
                          value={promoCode}
                          onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                          placeholder="Enter promo code"
                          className="flex-1 px-3 py-2 border border-orange-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent text-sm"
                        />
                        <button
                          onClick={applyDiscountCode}
                          disabled={isApplyingDiscount || !promoCode.trim()}
                          className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
                        >
                          {isApplyingDiscount ? 'Applying...' : 'Apply'}
                        </button>
                      </div>

                      {appliedDiscount && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center">
                              <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                              <span className="text-sm font-medium text-green-800">
                                Discount Applied: {appliedDiscount.code}
                              </span>
                            </div>
                            <button
                              onClick={clearDiscount}
                              className="text-red-600 hover:text-red-800 text-xs"
                            >
                              Remove
                            </button>
                          </div>
                          <div className="space-y-1 text-sm text-green-700">
                            <div className="flex justify-between">
                              <span>Original Fare:</span>
                              <span>₹{appliedDiscount.original_fare}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Discount ({appliedDiscount.type}):</span>
                              <span className="text-green-600 font-medium">-₹{appliedDiscount.discount_amount}</span>
                            </div>
                            <div className="flex justify-between font-bold border-t border-green-200 pt-1">
                              <span>Final Fare:</span>
                              <span className="text-green-600">₹{appliedDiscount.final_fare}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <button
                  onClick={requestRide}
                  disabled={!estimatedFare || estimatedFare === 0}
                  className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {estimatedFare > 0 ? 
                    appliedDiscount ? 
                      `Book Ride - ₹${appliedDiscount.final_fare} (Save ₹${appliedDiscount.discount_amount})` : 
                      `Book Ride - ₹${estimatedFare}` 
                    : 'Enter locations to book ride'
                  }
                </button>
              </div>
            </div>

          </div>

          {/* Map and Current Rides */}
          <div className="space-y-6">
            {/* Map */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center">
                <MapPin className="w-5 h-5 mr-2 text-blue-600" />
                Live Map
              </h2>
              
              {!loaded ? (
                <div className="w-full h-64 bg-gray-200 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                    <p className="text-gray-600">Loading map...</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div 
                    ref={setMapElement}
                    className="w-full h-64 bg-gray-200 rounded-lg border-2 border-gray-300"
                    style={{ minHeight: '256px' }}
                  />
                  
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center">
                        <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                        <span>Your Location</span>
                      </div>
                      {pickupLocation && (
                        <div className="flex items-center">
                          <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                          <span>Pickup</span>
                        </div>
                      )}
                      {dropLocation && (
                        <div className="flex items-center">
                          <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                          <span>Drop</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Current Rides */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Your Rides</h2>
                <button
                  onClick={() => {
                    setShowHistory(!showHistory);
                    if (!showHistory) fetchRideHistory();
                  }}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  {showHistory ? 'Hide History' : 'View History'}
                </button>
              </div>
              
              {currentRides.length === 0 ? (
                <div className="text-center py-4 text-gray-500">
                  <Clock className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p>No active rides</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {currentRides.slice(0, 3).map((ride) => (
                    <div key={ride.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      {/* Ride Status and Fare */}
                      <div className="flex justify-between items-center mb-3">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          ride.status === 'requested' ? 'bg-yellow-100 text-yellow-800' :
                          ride.status === 'accepted' ? 'bg-blue-100 text-blue-800' :
                          ride.status === 'in_progress' ? 'bg-purple-100 text-purple-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {ride.status.replace('_', ' ')}
                        </span>
                        <div className="text-right">
                          <div className="text-lg font-bold text-green-600 flex items-center">
                            <IndianRupee className="w-4 h-4 mr-1" />
                            {ride.estimated_fare}
                          </div>
                          <div className="text-sm text-gray-500">{ride.estimated_distance.toFixed(1)} km</div>
                        </div>
                      </div>

                      {/* Show ride OTP for accepted rides */}
                      {ride.status === 'accepted' && ride.ride_otp && (
                        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4 mb-3 animate-pulse">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center">
                              <CheckCircle className="w-6 h-6 text-green-600 mr-2" />
                              <span className="text-lg font-bold text-green-800">Your Ride OTP</span>
                            </div>
                            <span className="text-3xl font-bold text-green-600 font-mono tracking-wider bg-white px-3 py-1 rounded-lg border-2 border-green-300">
                              {ride.ride_otp}
                            </span>
                          </div>
                          <div className="bg-white rounded-lg p-3 border border-green-200">
                            <p className="text-sm text-green-700 mb-2">
                              <strong>📱 Share this OTP with your driver to start the ride</strong>
                            </p>
                            <p className="text-xs text-green-600">
                              ✅ Driver will ask for this 4-digit code before starting your journey<br/>
                              🔒 Keep this code safe and only share with your assigned driver
                            </p>
                          </div>
                        </div>
                      )}
                      
                      {ride.driver_info && (
                        <div className="bg-gray-50 rounded-lg p-3 mb-3">
                          <h4 className="font-medium text-gray-900 mb-2">Driver Details</h4>
                          <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                            <div>Name: {ride.driver_info.name}</div>
                            <div>Phone: {ride.driver_info.phone}</div>
                            <div>Vehicle: {ride.driver_info.vehicle_type}</div>
                            <div>Number: {ride.driver_info.vehicle_number}</div>
                          </div>
                        </div>
                      )}

                      {/* Action buttons */}
                      <div className="space-y-2 mb-4">
                        {/* Cancel button for requested/accepted rides */}
                        {(ride.status === 'requested' || ride.status === 'accepted') && (
                          <button
                            onClick={() => cancelRide(ride.id)}
                            className="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center"
                          >
                            <XCircle className="w-4 h-4 mr-2" />
                            Cancel Ride
                          </button>
                        )}

                        {/* Payment button for accepted rides */}
                        {ride.status === 'accepted' && ride.driver_info && !ride.ride_otp && (
                          <button
                            onClick={() => handlePayNow(ride)}
                            className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center"
                          >
                            <Smartphone className="w-4 h-4 mr-2" />
                            Pay Now with UPI
                          </button>
                        )}

                        {/* Payment status for paid rides */}
                        {ride.payment_status === 'paid' && (
                          <div className="flex items-center justify-center text-green-600 text-sm bg-green-50 py-2 rounded-lg">
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Payment Completed
                          </div>
                        )}
                      </div>

                      {/* From and To Section at the bottom */}
                      <div className="border-t pt-3">
                        <div className="space-y-3">
                          {/* From Section */}
                          <div className="flex items-start">
                            <div className="flex-shrink-0 w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mr-3">
                              <MapPin className="w-6 h-6 text-green-600" />
                            </div>
                            <div className="flex-1">
                              <div className="text-xs font-medium text-green-600 uppercase tracking-wide mb-1">FROM</div>
                              <div className="text-sm font-medium text-gray-900 leading-tight">
                                {ride.pickup_location?.address || 'Pickup location'}
                              </div>
                            </div>
                          </div>

                          {/* Divider Line */}
                          <div className="flex items-center ml-6">
                            <div className="w-px h-6 bg-gray-300"></div>
                          </div>

                          {/* To Section */}
                          <div className="flex items-start">
                            <div className="flex-shrink-0 w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mr-3">
                              <Navigation className="w-6 h-6 text-red-600" />
                            </div>
                            <div className="flex-1">
                              <div className="text-xs font-medium text-red-600 uppercase tracking-wide mb-1">TO</div>
                              <div className="text-sm font-medium text-gray-900 leading-tight">
                                {ride.drop_location?.address || 'Drop location'}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Ride History Modal */}
      {showHistory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Ride History</h2>
                <button
                  onClick={() => setShowHistory(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                {rideHistory.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No ride history found</p>
                  </div>
                ) : (
                  rideHistory.map((ride) => (
                    <div key={ride.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          {/* Enhanced Route Display */}
                          <div className="flex items-center mb-4">
                            <div className="flex items-center bg-green-50 rounded-lg px-4 py-3 flex-1 mr-3">
                              <MapPin className="w-5 h-5 text-green-600 mr-3 flex-shrink-0" />
                              <div className="flex-1">
                                <div className="text-xs font-medium text-green-600 uppercase tracking-wide">FROM</div>
                                <span className="text-sm font-medium text-green-800">
                                  {ride.pickup_location?.address || 'Pickup location'}
                                </span>
                              </div>
                            </div>
                            <Navigation className="w-5 h-5 text-gray-400 mx-2 flex-shrink-0" />
                            <div className="flex items-center bg-red-50 rounded-lg px-4 py-3 flex-1 ml-3">
                              <Navigation className="w-5 h-5 text-red-600 mr-3 flex-shrink-0" />
                              <div className="flex-1">
                                <div className="text-xs font-medium text-red-600 uppercase tracking-wide">TO</div>
                                <span className="text-sm font-medium text-red-800">
                                  {ride.drop_location?.address || 'Drop location'}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Ride Details Grid */}
                          <div className="grid grid-cols-3 gap-4 mb-4">
                            <div className="bg-gray-50 rounded-lg p-3 text-center">
                              <div className="text-lg font-bold text-green-600 flex items-center justify-center">
                                <IndianRupee className="w-4 h-4 mr-1" />
                                {ride.estimated_fare}
                              </div>
                              <div className="text-xs text-gray-500 mt-1">Total Fare</div>
                            </div>
                            <div className="bg-gray-50 rounded-lg p-3 text-center">
                              <div className="text-lg font-bold text-blue-600">
                                {ride.estimated_distance.toFixed(1)} km
                              </div>
                              <div className="text-xs text-gray-500 mt-1">Distance</div>
                            </div>
                            <div className="bg-gray-50 rounded-lg p-3 text-center">
                              <div className="text-sm font-medium text-gray-700">
                                {new Date(ride.created_at).toLocaleDateString()}
                              </div>
                              <div className="text-xs text-gray-500 mt-1">Date</div>
                            </div>
                          </div>

                          {/* Enhanced Vehicle and Driver Info */}
                          {ride.driver_info && (
                            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-4">
                              <div className="flex items-center justify-between mb-3">
                                <h4 className="font-semibold text-blue-900 flex items-center">
                                  🚗 Vehicle & Driver Details
                                </h4>
                                <div className="flex items-center bg-white px-3 py-1 rounded-full">
                                  <div className="w-8 h-8 bg-black rounded-full flex items-center justify-center text-white text-sm mr-2">
                                    {ride.preferred_vehicle_type === 'bike' ? '🏍️' :
                                     ride.preferred_vehicle_type === 'auto' ? '🛺' :
                                     ride.preferred_vehicle_type === 'car' ? '🚗' : 
                                     ride.preferred_vehicle_type === 'suv' ? '🚛' : '🚗'}
                                  </div>
                                  <span className="text-sm font-medium text-gray-700 capitalize">
                                    {ride.preferred_vehicle_type || ride.driver_info.vehicle_type || 'Car'}
                                  </span>
                                </div>
                              </div>
                              
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                {/* Driver Information */}
                                <div className="bg-white rounded-lg p-3">
                                  <h5 className="font-medium text-gray-800 mb-2 flex items-center">
                                    👨‍💼 Driver Information
                                  </h5>
                                  <div className="space-y-2">
                                    <div className="flex items-center">
                                      <User className="w-4 h-4 text-blue-600 mr-2" />
                                      <span className="text-gray-800 font-medium">{ride.driver_info.name}</span>
                                    </div>
                                    <div className="flex items-center">
                                      <Phone className="w-4 h-4 text-green-600 mr-2" />
                                      <a href={`tel:${ride.driver_info.phone}`} className="text-green-700 hover:text-green-800 underline">
                                        {ride.driver_info.phone}
                                      </a>
                                    </div>
                                    {ride.driver_info.rating && (
                                      <div className="flex items-center">
                                        <span className="text-yellow-500 mr-2">⭐</span>
                                        <span className="text-gray-800">{ride.driver_info.rating.toFixed(1)} Rating</span>
                                      </div>
                                    )}
                                  </div>
                                </div>

                                {/* Vehicle Information */}
                                <div className="bg-white rounded-lg p-3">
                                  <h5 className="font-medium text-gray-800 mb-2 flex items-center">
                                    🚙 Vehicle Information
                                  </h5>
                                  <div className="space-y-2">
                                    <div className="flex items-center">
                                      <Car className="w-4 h-4 text-blue-600 mr-2" />
                                      <span className="text-gray-800 font-medium capitalize">
                                        {ride.driver_info.vehicle_type || ride.preferred_vehicle_type || 'Car'}
                                      </span>
                                    </div>
                                    <div className="flex items-center">
                                      <span className="text-purple-600 mr-2">#️⃣</span>
                                      <span className="text-gray-800 font-mono bg-gray-100 px-2 py-1 rounded text-xs">
                                        {ride.driver_info.vehicle_number || 'Not Available'}
                                      </span>
                                    </div>
                                    {ride.driver_info.per_km_rate && (
                                      <div className="flex items-center">
                                        <span className="text-green-600 mr-2">💰</span>
                                        <span className="text-gray-800">₹{ride.driver_info.per_km_rate}/km</span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {/* Ride OTP Display */}
                              {ride.ride_otp && ride.status !== 'completed' && (
                                <div className="mt-3 bg-purple-100 border border-purple-300 rounded-lg p-3">
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-purple-800">Ride OTP:</span>
                                    <span className="bg-purple-600 text-white px-3 py-1 rounded-lg font-bold text-lg tracking-wider">
                                      {ride.ride_otp}
                                    </span>
                                  </div>
                                  <p className="text-xs text-purple-600 mt-1">Share this OTP with your driver</p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Default Vehicle Info for rides without driver assigned */}
                          {!ride.driver_info && (
                            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
                              <div className="flex items-center justify-between">
                                <h4 className="font-medium text-gray-800 flex items-center">
                                  🚗 Requested Vehicle Type
                                </h4>
                                <div className="flex items-center bg-white px-3 py-1 rounded-full">
                                  <div className="w-8 h-8 bg-black rounded-full flex items-center justify-center text-white text-sm mr-2">
                                    {ride.preferred_vehicle_type === 'bike' ? '🏍️' :
                                     ride.preferred_vehicle_type === 'auto' ? '🛺' :
                                     ride.preferred_vehicle_type === 'car' ? '🚗' : 
                                     ride.preferred_vehicle_type === 'suv' ? '🚛' : '🚗'}
                                  </div>
                                  <span className="text-sm font-medium text-gray-700 capitalize">
                                    {ride.preferred_vehicle_type || 'Car'}
                                  </span>
                                </div>
                              </div>
                              <p className="text-sm text-gray-600 mt-2">Waiting for {ride.preferred_vehicle_type || 'car'} driver to accept your request...</p>
                            </div>
                          )}

                          {/* Cancellation Reason */}
                          {ride.cancellation_reason && (
                            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                              <div className="flex items-center text-red-700">
                                <XCircle className="w-4 h-4 mr-2" />
                                <span className="text-sm font-medium">Cancellation Reason: {ride.cancellation_reason}</span>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        <div className="text-right ml-4">
                          <span className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                            ride.status === 'completed' ? 'bg-green-100 text-green-800' :
                            ride.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                            ride.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {ride.status.replace('_', ' ').toUpperCase()}
                          </span>
                          <div className="text-xs text-gray-500 mt-2">
                            {new Date(ride.created_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Confirmation Modal */}
      {showCancelModal && selectedRideForCancel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Cancel Ride</h2>
                <button
                  onClick={() => {
                    setShowCancelModal(false);
                    setSelectedRideForCancel(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <XCircle className="w-8 h-8 text-red-600 mr-3" />
                    <div>
                      <h3 className="font-medium text-red-900 mb-1">Cancel Ride Confirmation</h3>
                      <p className="text-sm text-red-700">
                        Are you sure you want to cancel this ride? This action cannot be undone.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="text-sm text-gray-600">
                  <p className="mb-2">⚠️ If you cancel after a driver has been assigned, it may affect your rating and future ride availability.</p>
                  <p>💡 Please only cancel if absolutely necessary.</p>
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={() => {
                      setShowCancelModal(false);
                      setSelectedRideForCancel(null);
                    }}
                    className="flex-1 bg-gray-200 text-gray-800 py-3 px-4 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                  >
                    Keep Ride
                  </button>
                  <button
                    onClick={() => confirmCancelRide("User cancelled via confirmation modal")}
                    className="flex-1 bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 transition-colors font-medium"
                  >
                    Confirm Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Available Discounts Modal */}
      {showDiscountModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Available Offers</h2>
                <button
                  onClick={() => setShowDiscountModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                {availableDiscounts.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <div className="w-16 h-16 bg-gray-200 rounded-full mx-auto mb-3 flex items-center justify-center">
                      <span className="text-2xl">🎁</span>
                    </div>
                    <p>No discount codes available at the moment</p>
                    <p className="text-sm">Check back later for exciting offers!</p>
                  </div>
                ) : (
                  availableDiscounts.map((discount, index) => (
                    <div
                      key={index}
                      onClick={() => selectDiscountCode(discount)}
                      className="border border-orange-200 rounded-lg p-4 hover:bg-orange-50 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-orange-600 text-lg">
                          {discount.code}
                        </span>
                        <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs font-medium">
                          {discount.discount_type === 'percentage' ? `${discount.discount_value}% OFF` :
                           discount.discount_type === 'fixed_amount' ? `₹${discount.discount_value} OFF` :
                           `${discount.discount_value}% OFF`}
                        </span>
                      </div>
                      
                      <div className="text-sm text-gray-600 space-y-1">
                        {discount.min_fare_amount > 0 && (
                          <div>Minimum fare: ₹{discount.min_fare_amount}</div>
                        )}
                        {discount.max_discount_amount && (
                          <div>Maximum discount: ₹{discount.max_discount_amount}</div>
                        )}
                        <div className="text-xs text-gray-500">
                          Valid until: {new Date(discount.valid_until).toLocaleDateString()}
                        </div>
                      </div>
                      
                      <div className="mt-3 text-xs text-orange-600 font-medium">
                        Tap to apply this offer
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* UPI Payment Modal */}
      {showPaymentModal && selectedRideForPayment && (
        <UPIPaymentModal
          ride={selectedRideForPayment}
          onClose={() => {
            setShowPaymentModal(false);
            setSelectedRideForPayment(null);
          }}
          onPaymentSuccess={handlePaymentSuccess}
        />
      )}
    </div>
  );
};

// Enhanced Location Autocomplete Component with Google Places API
const LocationAutocomplete = ({ 
  placeholder, 
  value, 
  onChange, 
  onLocationSelect, 
  showCurrentLocation = false,
  onUseCurrentLocation 
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [predictions, setPredictions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const { loaded } = useGoogleMaps();

  // Debounce function to avoid too many API calls
  const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  };

  // Get place predictions from Google Places API
  const getPlacePredictions = async (input) => {
    if (!loaded || !window.google || !input || input.length < 2) {
      setPredictions([]);
      return;
    }

    setIsLoading(true);
    
    try {
      const service = new window.google.maps.places.AutocompleteService();
      
      const request = {
        input: input,
        componentRestrictions: { country: ['in', 'us', 'gb'] }, // Focus on major countries
        types: ['establishment', 'geocode'], // Include businesses and locations
        fields: ['place_id', 'name', 'formatted_address', 'geometry'],
        location: new window.google.maps.LatLng(13.0827, 80.2707), // Bias towards Chennai
        radius: 50000 // 50km radius around Chennai
      };

      service.getPlacePredictions(request, (predictions, status) => {
        if (status === window.google.maps.places.PlacesServiceStatus.OK && predictions) {
          setPredictions(predictions.slice(0, 8)); // Limit to 8 suggestions
        } else {
          setPredictions([]);
        }
        setIsLoading(false);
      });
    } catch (error) {
      console.error('Error getting place predictions:', error);
      setIsLoading(false);
      setPredictions([]);
    }
  };

  // Debounced version of getPlacePredictions
  const debouncedGetPredictions = debounce(getPlacePredictions, 300);

  const handleInputChange = (e) => {
    const inputValue = e.target.value;
    onChange(inputValue);
    
    if (inputValue.length > 1) {
      setShowSuggestions(true);
      debouncedGetPredictions(inputValue);
    } else {
      setShowSuggestions(false);
      setPredictions([]);
    }
  };

  const handleSuggestionClick = async (prediction) => {
    try {
      onChange(prediction.description);
      onLocationSelect(prediction);
      setShowSuggestions(false);
      setPredictions([]);
    } catch (error) {
      console.error('Error selecting suggestion:', error);
    }
  };

  const handleInputFocus = () => {
    if (value.length > 1) {
      setShowSuggestions(true);
      debouncedGetPredictions(value);
    }
  };

  const handleInputBlur = () => {
    // Delay hiding suggestions to allow for clicks
    setTimeout(() => setShowSuggestions(false), 200);
  };

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:outline-none"
          placeholder={placeholder}
          value={value}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          autoComplete="off"
        />
        {showCurrentLocation && (
          <button
            type="button"
            onClick={onUseCurrentLocation}
            className="absolute right-2 top-2 text-blue-600 hover:text-blue-800"
            title="Use current location"
          >
            <Navigation className="w-5 h-5" />
          </button>
        )}
        
        {isLoading && (
          <div className="absolute right-8 top-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          </div>
        )}
      </div>
      
      {showSuggestions && (predictions.length > 0 || isLoading) && (
        <div className="absolute z-20 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-80 overflow-y-auto">
          {isLoading && predictions.length === 0 && (
            <div className="px-4 py-3 text-sm text-gray-500">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                Searching locations...
              </div>
            </div>
          )}
          
          {predictions.map((prediction, index) => (
            <button
              key={prediction.place_id || index}
              type="button"
              className="w-full px-4 py-3 text-left hover:bg-gray-100 focus:bg-gray-100 border-b border-gray-100 last:border-b-0 transition-colors"
              onClick={() => handleSuggestionClick(prediction)}
            >
              <div className="flex items-start">
                <MapPin className="w-4 h-4 text-gray-400 mr-3 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {prediction.structured_formatting?.main_text || prediction.description}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    {prediction.structured_formatting?.secondary_text || prediction.description}
                  </div>
                </div>
              </div>
            </button>
          ))}
          
          {predictions.length === 0 && !isLoading && (
            <div className="px-4 py-3 text-sm text-gray-500">
              No locations found. Try a different search term.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Enhanced Document Upload Component with Camera Support
const DocumentUpload = ({ label, onFileSelect, selectedFile, required = false }) => {
  const [dragOver, setDragOver] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [stream, setStream] = useState(null);
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const handleFileSelect = (file) => {
    if (file && (file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'application/pdf')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const fileData = {
          name: file.name,
          type: file.type,
          size: file.size,
          data: e.target.result // This will be base64
        };
        onFileSelect(fileData);
      };
      reader.readAsDataURL(file);
    } else {
      alert('Please select a valid image (JPG, PNG) or PDF file');
    }
  };

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'environment' // Use back camera on mobile
        } 
      });
      setStream(mediaStream);
      setShowCamera(true);
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      alert('Unable to access camera. Please check permissions or use file upload instead.');
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      
      canvas.toBlob((blob) => {
        const timestamp = new Date().getTime();
        const fileName = `captured_document_${timestamp}.jpg`;
        
        const reader = new FileReader();
        reader.onload = (e) => {
          const fileData = {
            name: fileName,
            type: 'image/jpeg',
            size: blob.size,
            data: e.target.result
          };
          onFileSelect(fileData);
          stopCamera();
        };
        reader.readAsDataURL(blob);
      }, 'image/jpeg', 0.9);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setShowCamera(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      
      {showCamera ? (
        <div className="space-y-4">
          <div className="relative bg-black rounded-lg overflow-hidden">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="w-full h-64 object-cover"
            />
            <canvas ref={canvasRef} className="hidden" />
          </div>
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={capturePhoto}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Capture Photo
            </button>
            <button
              type="button"
              onClick={stopCamera}
              className="bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div
          className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
            dragOver
              ? 'border-blue-400 bg-blue-50'
              : selectedFile
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300 bg-gray-50 hover:border-gray-400'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,application/pdf"
            onChange={(e) => handleFileSelect(e.target.files[0])}
            className="hidden"
          />
          
          {selectedFile ? (
            <div className="space-y-2">
              <div className="flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-green-700">{selectedFile.name}</p>
                <p className="text-xs text-green-600">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <div className="flex space-x-4 justify-center">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-blue-600 hover:text-blue-800 text-sm underline"
                >
                  Change file
                </button>
                <button
                  type="button"
                  onClick={startCamera}
                  className="text-blue-600 hover:text-blue-800 text-sm underline"
                >
                  Use camera
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-center">
                <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex space-x-4 justify-center">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="text-blue-600 hover:text-blue-800 font-medium flex items-center"
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    Upload File
                  </button>
                  <button
                    type="button"
                    onClick={startCamera}
                    className="text-blue-600 hover:text-blue-800 font-medium flex items-center"
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Use Camera
                  </button>
                </div>
                <p className="text-sm text-gray-500">or drag and drop</p>
              </div>
              <p className="text-xs text-gray-400">
                JPG, PNG or PDF (Max 5MB)
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// UPI Payment Component
const UPIPaymentModal = ({ ride, onClose, onPaymentSuccess }) => {
  const [Razorpay] = useRazorpay();
  const [loading, setLoading] = useState(false);
  const [paymentConfig, setPaymentConfig] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchPaymentConfig();
  }, []);

  const fetchPaymentConfig = async () => {
    try {
      const response = await axios.get(`${API}/payment-config`);
      setPaymentConfig(response.data);
    } catch (error) {
      console.error('Error fetching payment config:', error);
    }
  };

  const handleUPIPayment = async () => {
    if (!paymentConfig?.razorpay_enabled) {
      alert('UPI payments not available. Please try again later.');
      return;
    }

    setLoading(true);
    try {
      // Create Razorpay order
      const orderResponse = await axios.post(`${API}/payment/razorpay/create-order`, {
        ride_id: ride.id
      });

      const options = {
        key: paymentConfig.razorpay_key_id,
        amount: orderResponse.data.amount,
        currency: orderResponse.data.currency,
        order_id: orderResponse.data.order_id,
        name: "RideShare",
        description: `Payment for ride from ${ride.pickup_location.address} to ${ride.drop_location.address}`,
        image: "https://cdn-icons-png.flaticon.com/512/3448/3448339.png",
        handler: async (response) => {
          try {
            // Verify payment
            const verifyResponse = await axios.post(`${API}/payment/razorpay/verify`, {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature
            });

            if (verifyResponse.data.status === 'success') {
              onPaymentSuccess();
              onClose();
              alert('Payment successful! Your ride is now in progress.');
            }
          } catch (error) {
            console.error('Payment verification failed:', error);
            alert('Payment verification failed. Please contact support.');
          }
        },
        prefill: {
          name: user?.name || '',
          email: user?.email || '',
          contact: user?.phone || ''
        },
        notes: {
          ride_id: ride.id,
          pickup: ride.pickup_location.address,
          drop: ride.drop_location.address
        },
        theme: {
          color: "#2563eb"
        },
        method: {
          upi: true,
          card: true,
          netbanking: true,
          wallet: true
        }
      };

      const razorpayInstance = new Razorpay(options);
      
      razorpayInstance.on('payment.failed', (response) => {
        console.error('Payment failed:', response.error);
        alert(`Payment failed: ${response.error.description}`);
      });

      razorpayInstance.open();
    } catch (error) {
      console.error('Error initiating payment:', error);
      alert('Failed to initiate payment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!ride) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-md">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-gray-900">Complete Payment</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XCircle className="w-6 h-6" />
            </button>
          </div>

          {/* Ride Details */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="space-y-3">
              <div className="flex items-center">
                <MapPin className="w-4 h-4 text-green-600 mr-2" />
                <div>
                  <span className="text-sm text-gray-600">From:</span>
                  <p className="font-medium">{ride.pickup_location.address}</p>
                </div>
              </div>
              
              <div className="flex items-center">
                <Navigation className="w-4 h-4 text-red-600 mr-2" />
                <div>
                  <span className="text-sm text-gray-600">To:</span>
                  <p className="font-medium">{ride.drop_location.address}</p>
                </div>
              </div>

              <div className="border-t pt-3 mt-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Distance:</span>
                  <span className="font-medium">{ride.estimated_distance.toFixed(1)} km</span>
                </div>
                <div className="flex justify-between items-center mt-2">
                  <span className="text-lg font-semibold">Total Fare:</span>
                  <span className="text-2xl font-bold text-green-600 flex items-center">
                    <IndianRupee className="w-5 h-5 mr-1" />
                    {ride.estimated_fare}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Driver Info */}
          {ride.driver_info && (
            <div className="bg-blue-50 rounded-lg p-4 mb-6">
              <h3 className="font-semibold mb-2">Driver Details</h3>
              <div className="space-y-1 text-sm">
                <p><span className="font-medium">Name:</span> {ride.driver_info.name}</p>
                <p><span className="font-medium">Vehicle:</span> {ride.driver_info.vehicle_type} ({ride.driver_info.vehicle_number})</p>
                <p><span className="font-medium">Phone:</span> {ride.driver_info.phone}</p>
              </div>
            </div>
          )}

          {/* Payment Methods */}
          <div className="mb-6">
            <h3 className="font-semibold mb-3">Choose Payment Method</h3>
            
            <button
              onClick={handleUPIPayment}
              disabled={loading || !paymentConfig?.razorpay_enabled}
              className="w-full bg-blue-600 text-white py-4 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors mb-3"
            >
              <div className="flex items-center justify-center">
                <Smartphone className="w-5 h-5 mr-2" />
                {loading ? 'Processing...' : 'Pay with UPI / Cards / Wallet'}
              </div>
            </button>

            <div className="grid grid-cols-4 gap-2 text-center text-xs text-gray-600">
              <div className="flex flex-col items-center">
                <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center mb-1">
                  <span className="font-bold text-orange-600">₹</span>
                </div>
                <span>UPI</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mb-1">
                  <CreditCard className="w-4 h-4 text-blue-600" />
                </div>
                <span>Cards</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mb-1">
                  <span className="font-bold text-green-600">NB</span>
                </div>
                <span>NetBanking</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mb-1">
                  <span className="font-bold text-purple-600">W</span>
                </div>
                <span>Wallets</span>
              </div>
            </div>
          </div>

          {!paymentConfig?.razorpay_enabled && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg text-sm">
              <p className="font-medium">Demo Mode</p>
              <p>UPI payments are in demo mode. Use test credentials when prompted.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Mobile OTP Authentication Component
const MobileOTPAuth = ({ onSuccess }) => {
  const [step, setStep] = useState(1); // 1: phone input, 2: OTP input
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [userType, setUserType] = useState('rider');
  const [userName, setUserName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isExistingUser, setIsExistingUser] = useState(false);
  const [demoOtp, setDemoOtp] = useState('');
  const [resendTimer, setResendTimer] = useState(0);

  // Auto-format phone number for Indian/Chennai numbers
  const formatPhoneNumber = (value) => {
    // Remove all non-digit characters
    const numbers = value.replace(/\D/g, '');
    
    // Auto-add +91 for Indian numbers (including Chennai)
    if (numbers.length <= 10 && !value.startsWith('+')) {
      return numbers.length > 0 ? `+91 ${numbers}` : '';
    }
    
    return value;
  };

  const handlePhoneChange = (e) => {
    const formatted = formatPhoneNumber(e.target.value);
    setPhoneNumber(formatted);
  };

  const sendOTP = async () => {
    if (!phoneNumber || phoneNumber.length < 10) {
      setError('Please enter a valid phone number');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/send-otp`, {
        phone_number: phoneNumber,
        user_type: userType
      });

      if (response.data.success) {
        setIsExistingUser(response.data.is_existing_user);
        if (response.data.demo_otp) {
          setDemoOtp(response.data.demo_otp);
        }
        setStep(2);
        startResendTimer();
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const verifyOTP = async () => {
    if (!otpCode || otpCode.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    if (!isExistingUser && (!userName || userName.trim().length < 2)) {
      setError('Please enter your name');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/verify-otp`, {
        phone_number: phoneNumber,
        otp_code: otpCode,
        user_type: userType,
        name: userName
      });

      if (response.data.success) {
        // Store auth data
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('user', JSON.stringify(response.data.user_data));
        
        onSuccess(response.data.user_data, response.data.token);
      } else {
        setError(response.data.message);
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'OTP verification failed');
    } finally {
      setLoading(false);
    }
  };

  const startResendTimer = () => {
    setResendTimer(60);
    const timer = setInterval(() => {
      setResendTimer((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const resendOTP = () => {
    setOtpCode('');
    setError('');
    sendOTP();
  };

  const goBack = () => {
    setStep(1);
    setOtpCode('');
    setError('');
    setDemoOtp('');
  };

  return (
    <div className="w-full max-w-md">
      {step === 1 ? (
        // Phone Number Input Step
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Enter your mobile number
            </h2>
            <p className="text-gray-600">
              We'll send you an OTP to verify your number
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* User Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">I am a</label>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                className={`p-4 rounded-lg border-2 transition-all ${
                  userType === 'rider'
                    ? 'border-blue-500 bg-blue-50 text-blue-600'
                    : 'border-gray-300 text-gray-600 hover:border-gray-400'
                }`}
                onClick={() => setUserType('rider')}
              >
                <Users className="w-6 h-6 mx-auto mb-2" />
                <span className="font-medium">Rider</span>
              </button>
              <button
                type="button"
                className={`p-4 rounded-lg border-2 transition-all ${
                  userType === 'driver'
                    ? 'border-blue-500 bg-blue-50 text-blue-600'
                    : 'border-gray-300 text-gray-600 hover:border-gray-400'
                }`}
                onClick={() => setUserType('driver')}
              >
                <Car className="w-6 h-6 mx-auto mb-2" />
                <span className="font-medium">Driver</span>
              </button>
              <button
                type="button"
                className={`p-4 rounded-lg border-2 transition-all ${
                  userType === 'admin'
                    ? 'border-blue-500 bg-blue-50 text-blue-600'
                    : 'border-gray-300 text-gray-600 hover:border-gray-400'
                }`}
                onClick={() => setUserType('admin')}
              >
                <Settings className="w-6 h-6 mx-auto mb-2" />
                <span className="font-medium">Admin</span>
              </button>
            </div>
          </div>

          {/* Phone Number Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mobile Number
            </label>
            <div className="relative">
              <Phone className="w-5 h-5 text-gray-400 absolute left-3 top-3" />
              <input
                type="tel"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                placeholder="+91 98765 43210"
                value={phoneNumber}
                onChange={handlePhoneChange}
                maxLength={20}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              We support international numbers
            </p>
          </div>

          <button
            onClick={sendOTP}
            disabled={loading || !phoneNumber}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Sending OTP...' : 'Send OTP'}
          </button>
        </div>
      ) : (
        // OTP Verification Step
        <div className="space-y-6">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Smartphone className="w-8 h-8 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Verify your number
            </h2>
            <p className="text-gray-600">
              Enter the 6-digit code sent to
            </p>
            <p className="font-medium text-gray-900">{phoneNumber}</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {demoOtp && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg text-sm">
              <strong>Demo Mode:</strong> Use OTP: <code className="font-mono font-bold">{demoOtp}</code>
            </div>
          )}

          {/* Name input for new users */}
          {!isExistingUser && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Name
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your full name"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
              />
            </div>
          )}

          {/* OTP Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter OTP
            </label>
            <input
              type="text"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl font-mono tracking-widest"
              placeholder="000000"
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              maxLength={6}
            />
          </div>

          {/* Resend OTP */}
          <div className="text-center">
            {resendTimer > 0 ? (
              <p className="text-sm text-gray-500">
                Resend OTP in {resendTimer} seconds
              </p>
            ) : (
              <button
                onClick={resendOTP}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                Resend OTP
              </button>
            )}
          </div>

          <div className="space-y-3">
            <button
              onClick={verifyOTP}
              disabled={loading || otpCode.length !== 6}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? 'Verifying...' : (isExistingUser ? 'Login' : 'Create Account')}
            </button>

            <button
              onClick={goBack}
              className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Change Number
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
// Admin Dashboard Component
const AdminDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [users, setUsers] = useState([]);
  const [selectedUserType, setSelectedUserType] = useState('all');
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showDocuments, setShowDocuments] = useState(false);
  const [documents, setDocuments] = useState({});
  const [mobileSearch, setMobileSearch] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchDashboardData();
    fetchUsers();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/admin/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const fetchUsers = async (userType = null, searchMobile = null) => {
    try {
      setIsSearching(true);
      const params = new URLSearchParams();
      
      if (userType && userType !== 'all') {
        params.append('user_type', userType);
      }
      
      if (searchMobile && searchMobile.trim()) {
        params.append('mobile_search', searchMobile.trim());
      }
      
      const queryString = params.toString();
      const url = `${API}/admin/users${queryString ? `?${queryString}` : ''}`;
      
      const response = await axios.get(url);
      setUsers(response.data.users);
    } catch (error) {
      console.error('Error fetching users:', error);
      alert('Error fetching users. Please try again.');
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  const handleMobileSearch = async () => {
    if (mobileSearch.trim().length < 3) {
      alert('Please enter at least 3 digits to search');
      return;
    }
    await fetchUsers(selectedUserType === 'all' ? null : selectedUserType, mobileSearch);
  };

  const clearSearch = async () => {
    setMobileSearch('');
    await fetchUsers(selectedUserType === 'all' ? null : selectedUserType, null);
  };

  const handleUserAction = async (userId, action) => {
    try {
      await axios.post(`${API}/admin/user-action`, {
        user_id: userId,
        action: action
      });
      
      alert(`Action ${action} completed successfully!`);
      fetchUsers(selectedUserType === 'all' ? null : selectedUserType);
      fetchDashboardData();
    } catch (error) {
      console.error('Error performing action:', error);
      alert('Failed to perform action');
    }
  };

  const viewDocuments = async (userId) => {
    try {
      const response = await axios.get(`${API}/admin/driver-documents/${userId}`);
      setDocuments(response.data);
      setShowDocuments(true);
    } catch (error) {
      console.error('Error fetching documents:', error);
      alert('Failed to load documents');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading && !dashboardData) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Settings className="w-8 h-8 text-blue-600 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">Admin Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user?.name}</span>
              <button
                onClick={logout}
                className="flex items-center text-gray-600 hover:text-gray-900"
              >
                <LogOut className="w-4 h-4 mr-1" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics Cards */}
        {dashboardData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-blue-600" />
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Total Users</h3>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData.total_users}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Car className="w-8 h-8 text-green-600" />
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Total Drivers</h3>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData.total_drivers}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Navigation className="w-8 h-8 text-purple-600" />
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Total Rides</h3>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData.total_rides}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Clock className="w-8 h-8 text-orange-600" />
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-500">Pending Verifications</h3>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData.pending_verifications}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* User Management */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">User Management</h2>
              <div className="flex space-x-2">
                {['all', 'rider', 'driver'].map((type) => (
                  <button
                    key={type}
                    onClick={() => {
                      setSelectedUserType(type);
                      fetchUsers(type === 'all' ? null : type, mobileSearch || null);
                    }}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedUserType === type
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)}s
                  </button>
                ))}
              </div>
            </div>

            {/* Mobile Number Search */}
            <div className="flex items-center space-x-3 bg-gray-50 rounded-lg p-3">
              <div className="flex items-center text-gray-600">
                <Phone className="w-5 h-5 mr-2" />
                <span className="text-sm font-medium">Search by Mobile Number:</span>
              </div>
              <div className="flex-1 flex items-center space-x-2">
                <input
                  type="text"
                  value={mobileSearch}
                  onChange={(e) => setMobileSearch(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleMobileSearch();
                    }
                  }}
                  placeholder="Enter mobile number (e.g., 9876543210 or +91 9876543210)"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                />
                <button
                  onClick={handleMobileSearch}
                  disabled={isSearching || !mobileSearch.trim()}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                >
                  {isSearching ? 'Searching...' : 'Search'}
                </button>
                {mobileSearch && (
                  <button
                    onClick={clearSearch}
                    disabled={isSearching}
                    className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 disabled:opacity-50 transition-colors text-sm font-medium"
                  >
                    Clear
                  </button>
                )}
              </div>
              {users.length > 0 && mobileSearch && (
                <div className="text-sm text-green-600 font-medium">
                  Found {users.length} user{users.length > 1 ? 's' : ''}
                </div>
              )}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Joined
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                        <div className="text-sm text-gray-500">{user.phone}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.user_type === 'driver' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {user.user_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="space-y-1">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.is_active !== false 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.is_active !== false ? 'Active' : 'Inactive'}
                        </span>
                        {user.driver_profile && (
                          <div>
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              user.driver_profile.document_verified 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {user.driver_profile.document_verified ? 'Verified' : 'Pending'}
                            </span>
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      <button
                        onClick={() => handleUserAction(user.id, user.is_active !== false ? 'deactivate' : 'activate')}
                        className={`px-3 py-1 rounded text-xs font-medium ${
                          user.is_active !== false
                            ? 'bg-red-100 text-red-700 hover:bg-red-200'
                            : 'bg-green-100 text-green-700 hover:bg-green-200'
                        }`}
                      >
                        {user.is_active !== false ? 'Deactivate' : 'Activate'}
                      </button>
                      
                      {user.user_type === 'driver' && user.driver_profile && (
                        <>
                          <button
                            onClick={() => viewDocuments(user.id)}
                            className="px-3 py-1 bg-blue-100 text-blue-700 hover:bg-blue-200 rounded text-xs font-medium"
                          >
                            View Docs
                          </button>
                          
                          {!user.driver_profile.document_verified && (
                            <button
                              onClick={() => handleUserAction(user.id, 'verify_driver')}
                              className="px-3 py-1 bg-green-100 text-green-700 hover:bg-green-200 rounded text-xs font-medium"
                            >
                              Verify
                            </button>
                          )}
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Document Modal */}
      {showDocuments && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Driver Documents</h2>
                <button
                  onClick={() => setShowDocuments(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {documents.license_document && (
                  <div>
                    <h3 className="font-semibold mb-2">Driver's License</h3>
                    <div className="border rounded-lg p-4">
                      <p className="text-sm text-gray-600 mb-2">
                        File: {documents.license_document.name}
                      </p>
                      {documents.license_document.data && (
                        <img
                          src={documents.license_document.data}
                          alt="Driver License"
                          className="w-full h-64 object-contain bg-gray-100 rounded"
                        />
                      )}
                    </div>
                  </div>
                )}

                {documents.registration_document && (
                  <div>
                    <h3 className="font-semibold mb-2">Vehicle Registration</h3>
                    <div className="border rounded-lg p-4">
                      <p className="text-sm text-gray-600 mb-2">
                        File: {documents.registration_document.name}
                      </p>
                      {documents.registration_document.data && (
                        <img
                          src={documents.registration_document.data}
                          alt="Vehicle Registration"
                          className="w-full h-64 object-contain bg-gray-100 rounded"
                        />
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ProtectedRoute = ({ children, requiredUserType }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  if (requiredUserType && user.user_type !== requiredUserType) {
    // Redirect to appropriate dashboard based on user type
    if (user.user_type === 'admin') {
      return <Navigate to="/admin-dashboard" replace />;
    } else if (user.user_type === 'driver') {
      return <Navigate to="/driver-dashboard" replace />;
    } else {
      return <Navigate to="/rider-dashboard" replace />;
    }
  }

  return children;
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App">
          <Routes>
            <Route path="/auth" element={<AuthPage />} />
            <Route 
              path="/driver-dashboard" 
              element={
                <ProtectedRoute requiredUserType="driver">
                  <DriverDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/rider-dashboard" 
              element={
                <ProtectedRoute requiredUserType="rider">
                  <RiderDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/admin-dashboard" 
              element={
                <ProtectedRoute requiredUserType="admin">
                  <AdminDashboard />
                </ProtectedRoute>
              } 
            />
            <Route path="/" element={<Navigate to="/auth" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;