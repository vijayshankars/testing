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
const LegacyAuthForm = ({ onSwitch }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    phone: '',
    user_type: 'rider'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const url = isLogin ? `${API}/auth/login` : `${API}/auth/register`;
      const data = isLogin 
        ? { email: formData.email, password: formData.password }
        : formData;

      const response = await axios.post(url, data);
      
      login(response.data, response.data.token);
      
      if (response.data.user_type === 'driver') {
        navigate('/driver-dashboard');
      } else {
        navigate('/rider-dashboard');
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {!isLogin && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
              <input
                type="text"
                required
                className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
              <input
                type="tel"
                required
                className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">I am a</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  className={`p-3 rounded-lg border-2 transition-all ${
                    formData.user_type === 'rider'
                      ? 'border-blue-500 bg-blue-50 text-blue-600'
                      : 'border-gray-300 text-gray-600 hover:border-gray-400'
                  }`}
                  onClick={() => setFormData({ ...formData, user_type: 'rider' })}
                >
                  <Users className="w-5 h-5 mx-auto mb-1" />
                  Rider
                </button>
                <button
                  type="button"
                  className={`p-3 rounded-lg border-2 transition-all ${
                    formData.user_type === 'driver'
                      ? 'border-blue-500 bg-blue-50 text-blue-600'
                      : 'border-gray-300 text-gray-600 hover:border-gray-400'
                  }`}
                  onClick={() => setFormData({ ...formData, user_type: 'driver' })}
                >
                  <Car className="w-5 h-5 mx-auto mb-1" />
                  Driver
                </button>
              </div>
            </div>
          </>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
          <input
            type="email"
            required
            className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              required
              className="w-full px-3 py-3 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff className="w-5 h-5 text-gray-400" />
              ) : (
                <Eye className="w-5 h-5 text-gray-400" />
              )}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Sign Up')}
        </button>
      </form>

      <div className="mt-6 space-y-3">
        <div className="text-center">
          <button
            type="button"
            className="text-blue-600 hover:text-blue-500"
            onClick={() => setIsLogin(!isLogin)}
          >
            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
          </button>
        </div>
        
        <div className="text-center">
          <button
            type="button"
            className="text-sm text-gray-500 hover:text-gray-700"
            onClick={onSwitch}
          >
            Use mobile number instead
          </button>
        </div>
      </div>
    </div>
  );
};

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
const DriverDashboard = () => {
  const [driverProfile, setDriverProfile] = useState(null);
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [rideRequests, setRideRequests] = useState([]);
  const [acceptedRides, setAcceptedRides] = useState([]);
  const [rideHistory, setRideHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [isAvailable, setIsAvailable] = useState(false);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [profileForm, setProfileForm] = useState({
    vehicle_type: '',
    vehicle_number: '',
    license_number: '',
    license_document: null,
    registration_document: null
  });
  const [flashEffect, setFlashEffect] = useState(false);
  const [otpInput, setOtpInput] = useState('');
  const [selectedRideForOTP, setSelectedRideForOTP] = useState(null);
  const [isVerifyingLicense, setIsVerifyingLicense] = useState(false);
  const [licenseVerificationStatus, setLicenseVerificationStatus] = useState(null);
  const [isVerifyingVehicle, setIsVerifyingVehicle] = useState(false);
  const [vehicleVerificationStatus, setVehicleVerificationStatus] = useState(null);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [selectedRideForCancel, setSelectedRideForCancel] = useState(null);
  const [cancelReason, setCancelReason] = useState('');
  
  const { user, logout } = useAuth();
  const { getUserLocation } = useGoogleMaps();
  
  const verifyLicenseWithVahan = async () => {
    if (!profileForm.license_number) {
      alert('Please enter license number first');
      return;
    }
    
    setIsVerifyingLicense(true);
    setLicenseVerificationStatus(null);
    
    try {
      const response = await axios.post(`${API}/driver/verify-license`, {
        license_number: profileForm.license_number
      });
      
      if (response.data.success) {
        setLicenseVerificationStatus({
          success: true,
          message: 'License verified successfully with VAHAN system!',
          data: response.data.license_data
        });
      } else {
        setLicenseVerificationStatus({
          success: false,
          message: response.data.message || 'License verification failed'
        });
      }
    } catch (error) {
      console.error('License verification error:', error);
      setLicenseVerificationStatus({
        success: false,
        message: error.response?.data?.detail || 'License verification service unavailable. Please try again later.'
      });
    } finally {
      setIsVerifyingLicense(false);
    }
  };

  const verifyVehicleWithVahan = async () => {
    if (!profileForm.vehicle_number) {
      alert('Please enter vehicle number first');
      return;
    }
    
    setIsVerifyingVehicle(true);
    setVehicleVerificationStatus(null);
    
    try {
      const response = await axios.post(`${API}/driver/verify-vehicle`, {
        vehicle_number: profileForm.vehicle_number,
        vehicle_type: profileForm.vehicle_type
      });
      
      if (response.data.success) {
        setVehicleVerificationStatus({
          success: true,
          message: 'Vehicle verified successfully with VAHAN system!',
          data: response.data.vehicle_data
        });
      } else {
        setVehicleVerificationStatus({
          success: false,
          message: response.data.message || 'Vehicle verification failed'
        });
      }
    } catch (error) {
      console.error('Vehicle verification error:', error);
      setVehicleVerificationStatus({
        success: false,
        message: error.response?.data?.detail || 'Vehicle verification service unavailable. Please try again later.'
      });
    } finally {
      setIsVerifyingVehicle(false);
    }
  };
  
  // Use notification system
  const { notificationPermission } = useDriverNotifications(isAvailable, rideRequests);

  // Handle visual flash effect for new requests
  useEffect(() => {
    const handleNewRideRequest = (event) => {
      setFlashEffect(true);
      setTimeout(() => setFlashEffect(false), 2000);
    };

    window.addEventListener('newRideRequest', handleNewRideRequest);
    return () => window.removeEventListener('newRideRequest', handleNewRideRequest);
  }, []);

  useEffect(() => {
    fetchDriverProfile();
    getCurrentLocation();
  }, []);

  useEffect(() => {
    if (driverProfile && currentLocation) {
      updateDriverLocation();
      fetchRideRequests(); // Fetch immediately when location is available
      fetchAcceptedRides(); // Fetch accepted rides
      const interval = setInterval(() => {
        fetchRideRequests();
        fetchAcceptedRides();
      }, 10000); // Check every 10 seconds
      return () => clearInterval(interval);
    }
  }, [driverProfile, currentLocation]);

  const getCurrentLocation = async () => {
    try {
      const location = await getUserLocation();
      setCurrentLocation(location);
      console.log('Driver location updated:', location);
    } catch (error) {
      console.error('Error getting location:', error);
      // Try to use a fallback location for testing
      const fallbackLocation = { lat: 13.0827, lng: 80.2707 };
      setCurrentLocation(fallbackLocation);
      console.log('Using fallback location:', fallbackLocation);
    }
  };

  const updateDriverLocation = async () => {
    if (!currentLocation) return;
    
    try {
      await axios.put(`${API}/driver/location`, currentLocation);
      console.log('Driver location updated successfully');
    } catch (error) {
      console.error('Error updating location:', error);
    }
  };

  const fetchDriverProfile = async () => {
    try {
      const response = await axios.get(`${API}/driver/profile`);
      setDriverProfile(response.data);
      setIsAvailable(response.data.is_available);
    } catch (error) {
      if (error.response?.status === 404) {
        setShowProfileForm(true);
      }
    }
  };

  const fetchRideRequests = async () => {
    try {
      const response = await axios.get(`${API}/driver/ride-requests`);
      setRideRequests(response.data);
    } catch (error) {
      console.error('Error fetching ride requests:', error);
      // If location not set, show helpful message
      if (error.response?.status === 400 && error.response?.data?.detail?.includes('location not set')) {
        console.log('Driver location not set - updating location...');
        // Try to update location and retry
        if (currentLocation) {
          await updateDriverLocation();
          // Retry after location update
          setTimeout(() => fetchRideRequests(), 2000);
        }
      }
      // Set empty array to show "no requests" instead of error
      setRideRequests([]);
    }
  };

  const createDriverProfile = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/driver/profile`, profileForm);
      setShowProfileForm(false);
      fetchDriverProfile();
    } catch (error) {
      console.error('Error creating profile:', error);
    }
  };

  const toggleAvailability = async () => {
    try {
      const newAvailability = !isAvailable;
      await axios.put(`${API}/driver/availability/${newAvailability}`);
      setIsAvailable(newAvailability);
    } catch (error) {
      console.error('Error updating availability:', error);
    }
  };

  const acceptRide = async (rideId) => {
    try {
      const response = await axios.post(`${API}/driver/accept-ride/${rideId}`);
      
      // Remove the accepted ride from the list immediately
      setRideRequests(prevRequests => 
        prevRequests.filter(request => request.id !== rideId)
      );
      
      alert(`Ride accepted successfully! Ride OTP: ${response.data.ride_otp}\nShare this OTP with the rider for verification.`);
      
      // Refresh the lists
      setTimeout(() => {
        fetchRideRequests();
        fetchAcceptedRides();
      }, 2000);
      
    } catch (error) {
      console.error('Error accepting ride:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to accept ride';
      alert(`Error: ${errorMessage}`);
      
      fetchRideRequests();
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Car className="w-8 h-8 text-blue-600 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">Driver Dashboard</h1>
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
            
            {/* Accepted Rides */}
            {acceptedRides.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4 text-green-600">Your Active Rides</h2>
                <div className="space-y-4">
                  {acceptedRides.map((ride) => (
                    <div key={ride.id} className="border border-green-200 rounded-lg p-4 bg-green-50">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="flex items-center mb-2">
                            <MapPin className="w-4 h-4 text-green-600 mr-2" />
                            <span className="text-sm text-gray-600">From:</span>
                            <span className="ml-2 font-medium">{ride.pickup_location.address}</span>
                          </div>
                          <div className="flex items-center mb-3">
                            <Navigation className="w-4 h-4 text-red-600 mr-2" />
                            <span className="text-sm text-gray-600">To:</span>
                            <span className="ml-2 font-medium">{ride.drop_location.address}</span>
                          </div>
                          
                          <div className="grid grid-cols-3 gap-4 text-sm mb-3">
                            <div className="bg-white rounded p-2 text-center">
                              <div className="font-semibold text-green-600">₹{ride.estimated_fare}</div>
                              <div className="text-gray-600 text-xs">Fare</div>
                            </div>
                            <div className="bg-white rounded p-2 text-center">
                              <div className="font-semibold text-blue-600">{ride.estimated_distance.toFixed(1)} km</div>
                              <div className="text-gray-600 text-xs">Distance</div>
                            </div>
                            <div className="bg-white rounded p-2 text-center">
                              <div className="font-semibold text-purple-600">
                                {ride.ride_otp || '----'}
                              </div>
                              <div className="text-gray-600 text-xs">Ride OTP</div>
                            </div>
                          </div>

                          {ride.rider_info && (
                            <div className="text-sm text-gray-600 bg-white rounded p-2">
                              <div><strong>Rider:</strong> {ride.rider_info.name}</div>
                              <div><strong>Phone:</strong> {ride.rider_info.phone}</div>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex gap-2">
                        {ride.status === 'accepted' && (
                          <button
                            onClick={() => setSelectedRideForOTP(ride)}
                            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                          >
                            Verify OTP & Start
                          </button>
                        )}
                        
                        {ride.status === 'in_progress' && (
                          <button
                            onClick={() => completeRide(ride.id)}
                            className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
                          >
                            Complete Ride
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Nearby Ride Requests */}
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
                <button
                  onClick={toggleAvailability}
                  className="mt-4 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                >
                  Go Online
                </button>
              </div>
            ) : !currentLocation ? (
              <div className="text-center py-8 text-gray-500">
                <MapPin className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">Getting your location...</p>
                <p className="text-sm">Please enable location services</p>
              </div>
            ) : rideRequests.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Car className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">No ride requests nearby</p>
                <p className="text-sm">New requests will appear here automatically</p>
                <p className="text-xs text-gray-400 mt-2">
                  Searching within 25km radius • Last updated: {new Date().toLocaleTimeString()}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {rideRequests.map((request) => (
                  <div key={request.id} className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <MapPin className="w-4 h-4 text-green-600 mr-2" />
                          <span className="text-sm text-gray-600">From:</span>
                          <span className="ml-2 font-medium">{request.pickup_location.address}</span>
                        </div>
                        <div className="flex items-center mb-3">
                          <Navigation className="w-4 h-4 text-red-600 mr-2" />
                          <span className="text-sm text-gray-600">To:</span>
                          <span className="ml-2 font-medium">{request.drop_location.address}</span>
                        </div>
                        
                        {/* Request details in a grid */}
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div className="bg-gray-50 rounded p-2 text-center">
                            <div className="font-semibold text-blue-600">₹{request.estimated_fare}</div>
                            <div className="text-gray-600 text-xs">Fare</div>
                          </div>
                          <div className="bg-gray-50 rounded p-2 text-center">
                            <div className="font-semibold text-purple-600">{request.estimated_distance.toFixed(1)} km</div>
                            <div className="text-gray-600 text-xs">Trip Distance</div>
                          </div>
                          <div className="bg-gray-50 rounded p-2 text-center">
                            <div className="font-semibold text-orange-600">{request.distance_to_pickup} km</div>
                            <div className="text-gray-600 text-xs">To Pickup</div>
                          </div>
                        </div>
                        
                        {/* Request time */}
                        <div className="mt-2 text-xs text-gray-500">
                          Requested {new Date(request.created_at).toLocaleTimeString()}
                        </div>
                      </div>
                      
                      <div className="ml-4">
                        <button
                          onClick={() => acceptRide(request.id)}
                          className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium shadow-sm"
                        >
                          Accept Ride
                        </button>
                      </div>
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
                      Your OTP: {selectedRideForOTP.ride_otp}
                    </div>
                    <p className="text-sm text-blue-700">
                      📱 Share this code with the rider
                    </p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2">Ride Details:</h3>
                  <div className="space-y-1 text-sm text-gray-700">
                    <div><strong>From:</strong> {selectedRideForOTP.pickup_location?.address}</div>
                    <div><strong>To:</strong> {selectedRideForOTP.drop_location?.address}</div>
                    <div><strong>Fare:</strong> ₹{selectedRideForOTP.estimated_fare}</div>
                    <div><strong>Distance:</strong> {selectedRideForOTP.estimated_distance?.toFixed(1)} km</div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Enter OTP from Rider to Start Ride:
                  </label>
                  <input
                    type="text"
                    value={otpInput}
                    onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, '').slice(0, 4))}
                    placeholder="Enter 4-digit OTP"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl font-mono tracking-widest"
                    maxLength="4"
                    autoFocus
                  />
                  <p className="text-xs text-gray-500 mt-1 text-center">
                    Ask the rider to share the OTP displayed on their phone
                  </p>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="flex items-start">
                    <span className="text-yellow-600 mr-2">⚠️</span>
                    <div className="text-sm text-yellow-800">
                      <strong>Important:</strong> Only start the ride after the rider enters your vehicle and shares the correct OTP with you.
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
                    onClick={() => verifyRideOTP(selectedRideForOTP.id, otpInput)}
                    disabled={otpInput.length !== 4}
                    className="flex-1 bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    Start Ride
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
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
        estimated_fare: estimatedFare,
        promo_code: promoCode || null
      };

      const response = await axios.post(`${API}/rider/request-ride`, rideData);
      
      if (response.data.discount_applied) {
        alert(`🎉 Ride requested successfully with discount!\nOriginal fare: ₹${response.data.estimated_fare}\nDiscount: -₹${response.data.discount_applied.discount_amount}\nFinal fare: ₹${response.data.final_fare}\n\nWaiting for driver to accept...`);
      } else {
        alert('Ride requested successfully! Waiting for driver to accept...');
      }
      
      // Clear form after successful request
      clearLocations();
      clearDiscount();
      
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

            {/* Available Drivers */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Available Drivers Nearby</h2>
              
              {availableDrivers.length === 0 ? (
                <div className="text-center py-4 text-gray-500">
                  <Car className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p>No drivers available nearby</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {availableDrivers.slice(0, 5).map((driver, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                      <div>
                        <div className="font-medium">{driver.name}</div>
                        <div className="text-sm text-gray-600">
                          {driver.vehicle_type} • {driver.distance} km away
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-green-600">₹{driver.per_km_rate}/km</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
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

                          {/* Driver Info */}
                          {ride.driver_info && (
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                              <h4 className="font-medium text-blue-900 mb-2">Driver Details</h4>
                              <div className="grid grid-cols-2 gap-3 text-sm">
                                <div className="flex items-center">
                                  <User className="w-4 h-4 text-blue-600 mr-2" />
                                  <span className="text-blue-800">{ride.driver_info.name}</span>
                                </div>
                                <div className="flex items-center">
                                  <Phone className="w-4 h-4 text-blue-600 mr-2" />
                                  <span className="text-blue-800">{ride.driver_info.phone}</span>
                                </div>
                                <div className="flex items-center">
                                  <Car className="w-4 h-4 text-blue-600 mr-2" />
                                  <span className="text-blue-800">{ride.driver_info.vehicle_type}</span>
                                </div>
                                <div className="flex items-center">
                                  <span className="text-blue-600 mr-2">#</span>
                                  <span className="text-blue-800 font-mono">{ride.driver_info.vehicle_number}</span>
                                </div>
                              </div>
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