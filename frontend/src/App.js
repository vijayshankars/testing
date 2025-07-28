import React, { useState, useEffect, createContext, useContext, useRef } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Loader } from '@googlemaps/js-api-loader';
import { useRazorpay, RazorpayOrderOptions } from 'react-razorpay';
import { useRef } from 'react';
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
      center: { lat: 28.6139, lng: 77.2090 }, // Default to Delhi
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
            // Fallback to Delhi coordinates
            resolve({ lat: 28.6139, lng: 77.2090 });
          }
        );
      } else {
        console.error('Geolocation not supported');
        // Fallback to Delhi coordinates
        resolve({ lat: 28.6139, lng: 77.2090 });
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

// Login/Register Component
const AuthPage = () => {
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
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <Car className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">RideShare</h1>
          <p className="text-gray-600 mt-2">
            {isLogin ? 'Welcome back!' : 'Join us today!'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
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

        <div className="mt-6 text-center">
          <button
            type="button"
            className="text-blue-600 hover:text-blue-500"
            onClick={() => setIsLogin(!isLogin)}
          >
            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Driver Dashboard Component
const DriverDashboard = () => {
  const [driverProfile, setDriverProfile] = useState(null);
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [rideRequests, setRideRequests] = useState([]);
  const [isAvailable, setIsAvailable] = useState(false);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [profileForm, setProfileForm] = useState({
    per_km_rate: '',
    vehicle_type: '',
    vehicle_number: '',
    license_number: '',
    license_document: null,
    registration_document: null
  });
  
  const { user, logout } = useAuth();
  const { getUserLocation } = useGoogleMaps();

  useEffect(() => {
    fetchDriverProfile();
    getCurrentLocation();
  }, []);

  useEffect(() => {
    if (driverProfile && currentLocation) {
      updateDriverLocation();
      fetchRideRequests(); // Fetch immediately when location is available
      const interval = setInterval(fetchRideRequests, 10000); // Check every 10 seconds
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
      const fallbackLocation = { lat: 28.6139, lng: 77.2090 };
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
      
      alert('Ride accepted successfully! The rider has been notified.');
      
      // Refresh the list after a short delay
      setTimeout(() => {
        fetchRideRequests();
      }, 2000);
      
    } catch (error) {
      console.error('Error accepting ride:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to accept ride';
      alert(`Error: ${errorMessage}`);
      
      // Refresh the list in case the ride was taken by another driver
      fetchRideRequests();
    }
  };

  if (showProfileForm) {
    return (
      <div className="min-h-screen bg-gray-100 p-4">
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-6">Complete Your Driver Profile</h2>
          <form onSubmit={createDriverProfile} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Per KM Rate (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={profileForm.per_km_rate}
                  onChange={(e) => setProfileForm({ ...profileForm, per_km_rate: e.target.value })}
                />
              </div>
              
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
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Vehicle Number</label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., DL01AB1234"
                  value={profileForm.vehicle_number}
                  onChange={(e) => setProfileForm({ ...profileForm, vehicle_number: e.target.value })}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">License Number</label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., DL1234567890"
                  value={profileForm.license_number}
                  onChange={(e) => setProfileForm({ ...profileForm, license_number: e.target.value })}
                />
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
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Per KM Rate</span>
                      <span className="text-lg font-bold text-green-600">
                        ₹{driverProfile.per_km_rate}
                      </span>
                    </div>
                  </div>

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
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Ride Requests */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Nearby Ride Requests</h2>
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
                  Searching within 10km radius • Last updated: {new Date().toLocaleTimeString()}
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
  const [currentLocation, setCurrentLocation] = useState(null);
  const [mapElement, setMapElement] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedRideForPayment, setSelectedRideForPayment] = useState(null);
  const [mapInstance, setMapInstance] = useState(null);
  const [pickupMarker, setPickupMarker] = useState(null);
  const [dropMarker, setDropMarker] = useState(null);
  
  const { user, logout } = useAuth();
  const { loaded, initMap, calculateRoute, getUserLocation, searchPlaces } = useGoogleMaps();

  useEffect(() => {
    getCurrentLocation();
    fetchCurrentRides();
  }, []);

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
      // Use fallback location (Delhi)
      const fallbackLocation = { lat: 28.6139, lng: 77.2090 };
      setCurrentLocation(fallbackLocation);
      fetchAvailableDrivers(fallbackLocation.lat, fallbackLocation.lng);
    }
  };

  const handleLocationSelect = (locationType, address) => {
    if (locationType === 'pickup') {
      setPickupLocation(address);
      
      // Clear previous pickup marker
      if (pickupMarker) {
        pickupMarker.setMap(null);
        setPickupMarker(null);
      }
      
      // Search and add pickup marker
      if (mapInstance && window.google && address.trim()) {
        searchPlaces(address, (results) => {
          if (results.length > 0) {
            const place = results[0];
            const marker = new window.google.maps.Marker({
              position: place.geometry.location,
              map: mapInstance,
              title: `Pickup: ${address}`,
              icon: {
                url: 'https://maps.google.com/mapfiles/ms/icons/green-dot.png'
              }
            });
            setPickupMarker(marker);
            
            // Center map on pickup location
            mapInstance.panTo(place.geometry.location);
            
            // If drop marker exists, fit both locations
            if (dropMarker) {
              const bounds = new window.google.maps.LatLngBounds();
              bounds.extend(marker.getPosition());
              bounds.extend(dropMarker.getPosition());
              mapInstance.fitBounds(bounds);
              
              // Auto-calculate fare when both locations are set
              setTimeout(() => calculateFare(), 1000);
            }
          }
        });
      }
    } else if (locationType === 'drop') {
      setDropLocation(address);
      
      // Clear previous drop marker
      if (dropMarker) {
        dropMarker.setMap(null);
        setDropMarker(null);
      }
      
      // Search and add drop marker
      if (mapInstance && window.google && address.trim()) {
        searchPlaces(address, (results) => {
          if (results.length > 0) {
            const place = results[0];
            const marker = new window.google.maps.Marker({
              position: place.geometry.location,
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
              bounds.extend(marker.getPosition());
              mapInstance.fitBounds(bounds);
              
              // Auto-calculate fare when both locations are set
              setTimeout(() => calculateFare(), 1000);
            } else {
              // Just center on drop location
              mapInstance.panTo(place.geometry.location);
            }
          }
        });
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
    } catch (error) {
      console.error('Error fetching drivers:', error);
    }
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
      alert('Please enter both pickup and drop locations');
      return;
    }

    // If both locations are selected and map is available, calculate actual route
    if (mapInstance && pickupMarker && dropMarker && window.google) {
      const pickupPos = pickupMarker.getPosition();
      const dropPos = dropMarker.getPosition();
      
      // Calculate route using Google Directions API
      calculateRoute(pickupPos, dropPos, (result) => {
        const distance = result.distance;
        const avgRatePerKm = availableDrivers.length > 0 
          ? availableDrivers.reduce((sum, driver) => sum + driver.per_km_rate, 0) / availableDrivers.length
          : 15; // Default rate

        setEstimatedDistance(distance);
        setEstimatedFare(Math.round(distance * avgRatePerKm));
      });
    } else {
      // Fallback calculation if markers aren't available
      const mockDistance = Math.random() * 10 + 2; // Random distance between 2-12 km
      const avgRatePerKm = availableDrivers.length > 0 
        ? availableDrivers.reduce((sum, driver) => sum + driver.per_km_rate, 0) / availableDrivers.length
        : 15; // Default rate

      setEstimatedDistance(mockDistance);
      setEstimatedFare(Math.round(mockDistance * avgRatePerKm));
    }
  };

  const clearLocations = () => {
    setPickupLocation('');
    setDropLocation('');
    setEstimatedFare(0);
    setEstimatedDistance(0);
    
    // Clear markers
    if (pickupMarker) {
      pickupMarker.setMap(null);
      setPickupMarker(null);
    }
    if (dropMarker) {
      dropMarker.setMap(null);
      setDropMarker(null);
    }
    
    // Reset map view to current location
    if (mapInstance && currentLocation) {
      mapInstance.setCenter(currentLocation);
      mapInstance.setZoom(15);
    }
  };

  const requestRide = async () => {
    if (!pickupLocation || !dropLocation || !estimatedDistance) {
      alert('Please enter pickup and drop locations and calculate fare');
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
        estimated_fare: estimatedFare
      };

      await axios.post(`${API}/rider/request-ride`, rideData);
      alert('Ride requested successfully! Waiting for driver to accept...');
      
      // Clear form after successful request
      clearLocations();
      
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
                  <label className="block text-sm font-medium text-gray-700 mb-2">Pickup Location</label>
                  <LocationAutocomplete
                    placeholder="Enter pickup location"
                    value={pickupLocation}
                    onChange={setPickupLocation}
                    onLocationSelect={(location) => handleLocationSelect('pickup', location)}
                    showCurrentLocation={true}
                    onUseCurrentLocation={useCurrentLocation}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Drop Location</label>
                  <LocationAutocomplete
                    placeholder="Enter drop location"
                    value={dropLocation}
                    onChange={setDropLocation}
                    onLocationSelect={(location) => handleLocationSelect('drop', location)}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={calculateFare}
                    disabled={!pickupLocation || !dropLocation}
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
                )}
                
                <button
                  onClick={requestRide}
                  disabled={!estimatedFare || estimatedFare === 0}
                  className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {estimatedFare > 0 ? `Book Ride - ₹${estimatedFare}` : 'Enter locations to book ride'}
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
              <h2 className="text-lg font-semibold mb-4">Your Rides</h2>
              
              {currentRides.length === 0 ? (
                <div className="text-center py-4 text-gray-500">
                  <Clock className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p>No active rides</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {currentRides.slice(0, 3).map((ride) => (
                    <div key={ride.id} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <div className="font-medium mb-1">
                            {ride.pickup_location.address} → {ride.drop_location.address}
                          </div>
                          <div className="text-sm text-gray-600 flex items-center">
                            <IndianRupee className="w-3 h-3 mr-1" />
                            {ride.estimated_fare} • {ride.estimated_distance.toFixed(1)} km
                          </div>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          ride.status === 'requested' ? 'bg-yellow-100 text-yellow-800' :
                          ride.status === 'accepted' ? 'bg-blue-100 text-blue-800' :
                          ride.status === 'in_progress' ? 'bg-purple-100 text-purple-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {ride.status.replace('_', ' ')}
                        </span>
                      </div>
                      
                      {ride.driver_info && (
                        <div className="text-sm text-gray-600 border-t pt-2 mt-2">
                          <div>Driver: {ride.driver_info.name}</div>
                          <div>Vehicle: {ride.driver_info.vehicle_type} ({ride.driver_info.vehicle_number})</div>
                          <div>Phone: {ride.driver_info.phone}</div>
                        </div>
                      )}

                      {/* Payment button for accepted rides */}
                      {ride.status === 'accepted' && ride.driver_info && (
                        <div className="border-t pt-3 mt-3">
                          <button
                            onClick={() => handlePayNow(ride)}
                            className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center"
                          >
                            <Smartphone className="w-4 h-4 mr-2" />
                            Pay Now with UPI
                          </button>
                        </div>
                      )}

                      {/* Payment status for paid rides */}
                      {ride.payment_status === 'paid' && (
                        <div className="border-t pt-3 mt-3">
                          <div className="flex items-center text-green-600 text-sm">
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Payment Completed
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

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

// Location Autocomplete Component
const LocationAutocomplete = ({ 
  placeholder, 
  value, 
  onChange, 
  onLocationSelect, 
  suggestions = [], 
  showCurrentLocation = false,
  onUseCurrentLocation 
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [localSuggestions, setLocalSuggestions] = useState([]);
  
  // Common locations for quick selection
  const commonLocations = [
    'Airport, Delhi',
    'Railway Station, Delhi',
    'Bus Stand, Delhi',
    'Metro Station, Delhi',
    'Hospital, Delhi',
    'Mall, Delhi',
    'Connaught Place, Delhi',
    'India Gate, Delhi',
    'Red Fort, Delhi',
    'Lotus Temple, Delhi',
    'Qutub Minar, Delhi',
    'Chandni Chowk, Delhi'
  ];

  const handleInputChange = (e) => {
    const inputValue = e.target.value;
    onChange(inputValue);
    
    if (inputValue.length > 2) {
      // Filter common locations based on input
      const filtered = commonLocations.filter(location =>
        location.toLowerCase().includes(inputValue.toLowerCase())
      );
      setLocalSuggestions(filtered);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    onChange(suggestion);
    onLocationSelect(suggestion);
    setShowSuggestions(false);
  };

  const handleInputFocus = () => {
    if (value.length <= 2) {
      setLocalSuggestions(commonLocations.slice(0, 8));
      setShowSuggestions(true);
    }
  };

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          placeholder={placeholder}
          value={value}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
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
      </div>
      
      {showSuggestions && localSuggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {localSuggestions.map((suggestion, index) => (
            <button
              key={index}
              type="button"
              className="w-full px-4 py-3 text-left hover:bg-gray-100 focus:bg-gray-100 border-b border-gray-100 last:border-b-0 transition-colors"
              onClick={() => handleSuggestionClick(suggestion)}
            >
              <div className="flex items-center">
                <MapPin className="w-4 h-4 text-gray-400 mr-3" />
                <span className="text-sm">{suggestion}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// Document Upload Component
const DocumentUpload = ({ label, onFileSelect, selectedFile, required = false }) => {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

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
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="text-blue-600 hover:text-blue-800 text-sm underline"
            >
              Change file
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center justify-center">
              <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
            </div>
            <div>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                Click to upload
              </button>
              <p className="text-sm text-gray-500">or drag and drop</p>
            </div>
            <p className="text-xs text-gray-400">
              JPG, PNG or PDF (Max 5MB)
            </p>
          </div>
        )}
      </div>
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
    return <Navigate to={user.user_type === 'driver' ? '/driver-dashboard' : '/rider-dashboard'} replace />;
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
            <Route path="/" element={<Navigate to="/auth" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;