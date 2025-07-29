import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  MapPin, 
  Navigation, 
  Clock, 
  DollarSign, 
  Phone, 
  CheckCircle, 
  XCircle,
  User,
  Car,
  Eye,
  EyeOff,
  RefreshCw,
  Star
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : 'http://localhost:8001/api';

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
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedRideForReject, setSelectedRideForReject] = useState(null);
  const [rejectReason, setRejectReason] = useState('');

  // Get user and logout from localStorage/context (simplified approach)
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/auth';
  };

  // Get user location (simplified approach)
  const getUserLocation = () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }
      
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => reject(error)
      );
    });
  };

  // Vehicle icons mapping
  const getVehicleIcon = (vehicleType) => {
    const iconBase = {
      width: '48px',
      height: '48px',
      borderRadius: '50%',
      backgroundColor: '#000000',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    };

    const svgProps = {
      width: '28',
      height: '28',
      fill: 'white',
      stroke: 'white',
      strokeWidth: '1'
    };

    switch (vehicleType?.toLowerCase()) {
      case 'bike':
        return (
          <div style={iconBase}>
            <svg {...svgProps} viewBox="0 0 24 24">
              <circle cx="5" cy="16" r="3"/>
              <circle cx="19" cy="16" r="3"/>
              <path d="M8 16h8"/>
              <path d="M12 6l4 5h-3l-2-3-2 3H6l4-5z"/>
            </svg>
          </div>
        );
      case 'auto':
        return (
          <div style={iconBase}>
            <svg {...svgProps} viewBox="0 0 24 24">
              <path d="M3 16a3 3 0 003 3h12a3 3 0 003-3M21 16V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8"/>
              <circle cx="7" cy="16" r="2"/>
              <circle cx="17" cy="16" r="2"/>
              <path d="M3 8l2-4h14l2 4"/>
            </svg>
          </div>
        );
      case 'suv':
        return (
          <div style={iconBase}>
            <svg {...svgProps} viewBox="0 0 24 24">
              <rect x="2" y="6" width="20" height="10" rx="2"/>
              <circle cx="7" cy="16" r="2"/>
              <circle cx="17" cy="16" r="2"/>
              <path d="M2 10h20"/>
              <path d="M6 6V4a2 2 0 012-2h6a2 2 0 012 2v2"/>
            </svg>
          </div>
        );
      default: // car
        return (
          <div style={iconBase}>
            <svg {...svgProps} viewBox="0 0 24 24">
              <path d="M3 16a3 3 0 003 3h12a3 3 0 003-3"/>
              <path d="M21 16V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8"/>
              <circle cx="7" cy="16" r="2"/>
              <circle cx="17" cy="16" r="2"/>
              <path d="M3 8l2-4h14l2 4"/>
            </svg>
          </div>
        );
    }
  };

  // Helper function to get vehicle emoji
  const getVehicleEmoji = (vehicleType) => {
    switch (vehicleType?.toLowerCase()) {
      case 'bike': return '🏍️';
      case 'auto': return '🛺';
      case 'car': return '🚗';
      case 'suv': return '🚛';
      default: return '🚗';
    }
  };

  // Set up axios interceptor for authentication
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  // Fetch driver profile on component mount
  useEffect(() => {
    fetchDriverProfile();
    getCurrentLocation();
  }, []);

  // Flash effect for new ride requests
  useEffect(() => {
    const handleNewRideRequest = () => {
      setFlashEffect(true);
      setTimeout(() => setFlashEffect(false), 2000);
    };

    window.addEventListener('newRideRequest', handleNewRideRequest);
    return () => window.removeEventListener('newRideRequest', handleNewRideRequest);
  }, []);

  // Auto-refresh ride requests and accepted rides
  useEffect(() => {
    if (driverProfile && currentLocation) {
      fetchRideRequests();
      fetchAcceptedRides();
      const interval = setInterval(() => {
        fetchRideRequests();
        fetchAcceptedRides();
      }, 10000); // Check every 10 seconds
      return () => clearInterval(interval);
    }
  }, [driverProfile, currentLocation]);

  // Get current location
  const getCurrentLocation = async () => {
    try {
      const location = await getUserLocation();
      setCurrentLocation(location);
      
      if (driverProfile && location) {
        await updateDriverLocation(location.lat, location.lng);
      }
    } catch (error) {
      console.error('Error getting location:', error);
    }
  };

  // Fetch driver profile
  const fetchDriverProfile = async () => {
    try {
      const response = await axios.get(`${API}/driver/profile`);
      if (response.data.success) {
        setDriverProfile(response.data.profile);
        setIsAvailable(response.data.profile.is_available || false);
      } else {
        setShowProfileForm(true);
      }
    } catch (error) {
      console.error('Error fetching driver profile:', error);
      setShowProfileForm(true);
    }
  };

  // Update driver location
  const updateDriverLocation = async (lat, lng) => {
    try {
      await axios.put(`${API}/driver/location`, {
        current_location: { lat, lng }
      });
    } catch (error) {
      console.error('Error updating location:', error);
    }
  };

  // Toggle driver availability
  const toggleAvailability = async () => {
    try {
      const newAvailability = !isAvailable;
      const response = await axios.put(`${API}/driver/availability/${newAvailability}`);
      if (response.data.success) {
        setIsAvailable(newAvailability);
        setDriverProfile(prev => ({ ...prev, is_available: newAvailability }));
      }
    } catch (error) {
      console.error('Error toggling availability:', error);
      alert('Failed to update availability');
    }
  };

  // Fetch ride requests
  const fetchRideRequests = async () => {
    try {
      const response = await axios.get(`${API}/driver/ride-requests`);
      if (response.data.success) {
        setRideRequests(response.data.ride_requests);
      }
    } catch (error) {
      console.error('Error fetching ride requests:', error);
    }
  };

  // Fetch accepted rides
  const fetchAcceptedRides = async () => {
    try {
      const response = await axios.get(`${API}/driver/accepted-rides`);
      if (response.data.success) {
        setAcceptedRides(response.data.rides);
      }
    } catch (error) {
      console.error('Error fetching accepted rides:', error);
    }
  };

  // Accept ride
  const acceptRide = async (rideId) => {
    try {
      const response = await axios.post(`${API}/driver/accept-ride/${rideId}`);
      if (response.data.success) {
        alert(`✅ Ride accepted! OTP: ${response.data.ride_otp}`);
        fetchRideRequests();
        fetchAcceptedRides();
      }
    } catch (error) {
      console.error('Error accepting ride:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to accept ride';
      alert('❌ ' + errorMessage);
    }
  };

  // Reject ride
  const rejectRide = async (rideId, reason) => {
    try {
      const response = await axios.post(`${API}/driver/reject-ride/${rideId}`, { reason });
      if (response.data.success) {
        alert('✅ Ride rejected successfully');
        fetchRideRequests();
      }
    } catch (error) {
      console.error('Error rejecting ride:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to reject ride';
      alert('❌ ' + errorMessage);
    }
  };

  // Handle reject ride
  const handleRejectRide = (ride) => {
    setSelectedRideForReject(ride);
    setShowRejectModal(true);
  };

  // Confirm reject ride
  const confirmRejectRide = async () => {
    if (selectedRideForReject && rejectReason) {
      await rejectRide(selectedRideForReject.id, rejectReason);
      setShowRejectModal(false);
      setSelectedRideForReject(null);
      setRejectReason('');
    }
  };

  // Verify OTP and start ride
  const verifyOtpAndStartRide = async () => {
    if (!otpInput || !selectedRideForOTP) return;

    try {
      const response = await axios.post(`${API}/driver/verify-ride-otp`, {
        ride_id: selectedRideForOTP.id,
        otp: otpInput
      });

      if (response.data.success) {
        alert('✅ Ride started successfully!');
        setSelectedRideForOTP(null);
        setOtpInput('');
        fetchAcceptedRides();
      }
    } catch (error) {
      console.error('Error verifying OTP:', error);
      const errorMessage = error.response?.data?.detail || 'Invalid OTP';
      alert('❌ ' + errorMessage);
    }
  };

  // Complete ride
  const completeRide = async (rideId) => {
    try {
      const response = await axios.post(`${API}/driver/complete-ride`, {
        ride_id: rideId
      });

      if (response.data.success) {
        alert('✅ Ride completed successfully!');
        fetchAcceptedRides();
        fetchRideHistory();
      }
    } catch (error) {
      console.error('Error completing ride:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to complete ride';
      alert('❌ ' + errorMessage);
    }
  };

  // Cancel ride
  const cancelRide = async (rideId, reason) => {
    try {
      const response = await axios.post(`${API}/driver/cancel-ride/${rideId}`, { reason });
      if (response.data.success) {
        alert('✅ Ride cancelled successfully');
        fetchAcceptedRides();
        fetchRideHistory();
      }
    } catch (error) {
      console.error('Error cancelling ride:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to cancel ride';
      alert('❌ ' + errorMessage);
    }
  };

  // Handle cancel ride
  const handleCancelRide = (ride) => {
    setSelectedRideForCancel(ride);
    setShowCancelModal(true);
  };

  // Confirm cancel ride
  const confirmCancelRide = async () => {
    if (selectedRideForCancel && cancelReason) {
      await cancelRide(selectedRideForCancel.id, cancelReason);
      setShowCancelModal(false);
      setSelectedRideForCancel(null);
      setCancelReason('');
    }
  };

  // Fetch ride history
  const fetchRideHistory = async () => {
    try {
      const response = await axios.get(`${API}/driver/ride-history`);
      if (response.data.success) {
        setRideHistory(response.data.rides);
      }
    } catch (error) {
      console.error('Error fetching ride history:', error);
    }
  };

  // Create driver profile (VAHAN integration functions would go here)
  const createDriverProfile = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/driver/profile`, profileForm);
      if (response.data.success) {
        setDriverProfile(response.data.profile);
        setShowProfileForm(false);
        alert('✅ Driver profile created successfully!');
      }
    } catch (error) {
      console.error('Error creating profile:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to create profile';
      alert('❌ ' + errorMessage);
    }
  };

  // Initialize Google Map for current ride
  const initializeCurrentRideMap = (ride) => {
    if (!window.google || !window.google.maps) return;

    const mapElement = document.getElementById(`current-ride-map-${ride.id}`);
    if (!mapElement) return;

    const map = new window.google.maps.Map(mapElement, {
      zoom: 13,
      center: ride.pickup_location,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false
    });

    // Add pickup marker
    new window.google.maps.Marker({
      position: ride.pickup_location,
      map: map,
      title: 'Pickup Location',
      icon: {
        path: window.google.maps.SymbolPath.CIRCLE,
        scale: 8,
        fillColor: '#10B981',
        fillOpacity: 1,
        strokeColor: '#fff',
        strokeWeight: 2
      }
    });

    // Add drop marker
    new window.google.maps.Marker({
      position: ride.drop_location,
      map: map,
      title: 'Drop Location',
      icon: {
        path: window.google.maps.SymbolPath.CIRCLE,
        scale: 8,
        fillColor: '#EF4444',
        fillOpacity: 1,
        strokeColor: '#fff',
        strokeWeight: 2
      }
    });

    // Add driver marker with vehicle icon
    if (currentLocation) {
      const vehicleIcon = {
        url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
          <svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
            <circle cx="24" cy="24" r="24" fill="#000000"/>
            <g fill="white" stroke="white" stroke-width="1" transform="translate(12,12)">
              <path d="M3 16a3 3 0 003 3h12a3 3 0 003-3"/>
              <path d="M21 16V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8"/>
              <circle cx="7" cy="16" r="2"/>
              <circle cx="17" cy="16" r="2"/>
              <path d="M3 8l2-4h14l2 4"/>
            </g>
          </svg>
        `)}`,
        scaledSize: new window.google.maps.Size(48, 48)
      };

      new window.google.maps.Marker({
        position: currentLocation,
        map: map,
        title: 'Your Location',
        icon: vehicleIcon
      });
    }

    // Draw route
    const directionsService = new window.google.maps.DirectionsService();
    const directionsRenderer = new window.google.maps.DirectionsRenderer({
      strokeColor: '#3B82F6',
      strokeWeight: 4
    });

    directionsRenderer.setMap(map);

    directionsService.route({
      origin: ride.pickup_location,
      destination: ride.drop_location,
      travelMode: window.google.maps.TravelMode.DRIVING
    }, (result, status) => {
      if (status === 'OK') {
        directionsRenderer.setDirections(result);
      }
    });
  };

  // Use effect to initialize maps when accepted rides change
  useEffect(() => {
    if (acceptedRides.length > 0) {
      setTimeout(() => {
        acceptedRides.forEach(ride => {
          initializeCurrentRideMap(ride);
        });
      }, 100);
    }
  }, [acceptedRides, currentLocation]);

  // Render profile form if needed
  if (showProfileForm) {
    return (
      <div className="min-h-screen bg-gray-100 p-4">
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-6">Complete Your Driver Profile</h2>
          <form onSubmit={createDriverProfile} className="space-y-6">
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Vehicle Type *
                </label>
                <select
                  value={profileForm.vehicle_type}
                  onChange={(e) => setProfileForm({...profileForm, vehicle_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select Vehicle Type</option>
                  <option value="bike">Bike</option>
                  <option value="auto">Auto Rickshaw</option>
                  <option value="car">Car</option>
                  <option value="suv">SUV</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Vehicle Number *
                </label>
                <input
                  type="text"
                  value={profileForm.vehicle_number}
                  onChange={(e) => setProfileForm({...profileForm, vehicle_number: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., KA01AB1234"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  License Number *
                </label>
                <input
                  type="text"
                  value={profileForm.license_number}
                  onChange={(e) => setProfileForm({...profileForm, license_number: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., DL-1420110012345"
                  required
                />
              </div>
            </div>
            
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Create Profile
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
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    isAvailable 
                      ? 'bg-green-600 text-white hover:bg-green-700' 
                      : 'bg-gray-600 text-white hover:bg-gray-700'
                  }`}
                >
                  {isAvailable ? 'Online' : 'Offline'}
                </button>
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
                        <span className="text-sm text-gray-600">Rate</span>
                        <span className="text-sm font-medium">₹{driverProfile.per_km_rate}/km</span>
                      </div>
                    </div>
                  </div>
                </>
              )}

              <button
                onClick={() => {
                  setShowHistory(!showHistory);
                  if (!showHistory) fetchRideHistory();
                }}
                className="w-full bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors font-medium flex items-center justify-center"
              >
                {showHistory ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
                {showHistory ? 'Hide History' : 'View History'}
              </button>
            </div>
          </div>

          {/* Current Rides - Live Navigation (Only show when there are accepted rides) */}
          {acceptedRides.length > 0 && (
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4 text-green-600">Current Ride - Live Navigation</h2>
              
              {acceptedRides.map((ride) => (
                <div key={ride.id} className="mb-6">
                  {/* Ride Status Banner */}
                  <div className={`p-4 rounded-lg mb-4 ${
                    ride.status === 'accepted' ? 'bg-yellow-100 border-l-4 border-yellow-500' :
                    ride.status === 'in_progress' ? 'bg-green-100 border-l-4 border-green-500' :
                    'bg-blue-100 border-l-4 border-blue-500'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-lg">
                          {ride.status === 'accepted' ? '🟡 Ride Accepted' :
                           ride.status === 'in_progress' ? '🟢 Ride In Progress' :
                           '🔵 Ride Status'}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {ride.pickup_address} → {ride.drop_address}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">₹{ride.estimated_fare}</p>
                        <p className="text-sm text-gray-600">{ride.estimated_distance} km</p>
                      </div>
                    </div>
                  </div>

                  {/* Enhanced Google Maps */}
                  <div className="mb-4">
                    <div className="bg-gradient-to-r from-blue-50 to-green-50 p-4 rounded-lg mb-3">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-800">
                          {ride.status === 'in_progress' ? 'Live Trip Tracking' : 'Route Navigation'}
                        </h4>
                        {ride.status === 'in_progress' && (
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse mr-2"></div>
                            <span className="text-sm font-medium text-red-600">LIVE</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div 
                      id={`current-ride-map-${ride.id}`} 
                      className={`w-full rounded-lg ${ride.status === 'in_progress' ? 'h-96 border-2 border-green-400' : 'h-80'}`}
                      style={{ minHeight: '320px' }}
                    ></div>
                    
                    {/* Map Controls */}
                    <div className="flex justify-between mt-3">
                      <button
                        onClick={() => initializeCurrentRideMap(ride)}
                        className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Refresh Map
                      </button>
                      <button
                        onClick={() => {
                          const url = `https://www.google.com/maps/dir/${ride.pickup_location.lat},${ride.pickup_location.lng}/${ride.drop_location.lat},${ride.drop_location.lng}`;
                          window.open(url, '_blank');
                        }}
                        className="flex items-center px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                      >
                        <Navigation className="w-4 h-4 mr-2" />
                        Open in Google Maps
                      </button>
                    </div>
                  </div>

                  {/* Live Trip Status (for in-progress rides) */}
                  {ride.status === 'in_progress' && (
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="bg-green-50 p-3 rounded-lg text-center">
                        <Clock className="w-5 h-5 mx-auto mb-1 text-green-600" />
                        <p className="text-sm font-medium text-green-800">Trip Time</p>
                        <p className="text-xs text-green-600">{new Date().toLocaleTimeString()}</p>
                      </div>
                      <div className="bg-green-50 p-3 rounded-lg text-center">
                        <MapPin className="w-5 h-5 mx-auto mb-1 text-green-600" />
                        <p className="text-sm font-medium text-green-800">Distance</p>
                        <p className="text-xs text-green-600">{ride.estimated_distance} km</p>
                      </div>
                      <div className="bg-green-50 p-3 rounded-lg text-center">
                        <DollarSign className="w-5 h-5 mx-auto mb-1 text-green-600" />
                        <p className="text-sm font-medium text-green-800">Fare</p>
                        <p className="text-xs text-green-600">₹{ride.estimated_fare}</p>
                      </div>
                    </div>
                  )}

                  {/* Rider Information */}
                  <div className="bg-gradient-to-r from-gray-50 to-blue-50 p-4 rounded-lg mb-4">
                    <h4 className="font-semibold mb-2">Rider Information</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Name</p>
                        <p className="font-medium">{ride.rider_name}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Phone</p>
                        <a 
                          href={`tel:${ride.rider_phone}`}
                          className="font-medium text-blue-600 hover:text-blue-800 flex items-center"
                        >
                          <Phone className="w-4 h-4 mr-1" />
                          {ride.rider_phone}
                        </a>
                      </div>
                    </div>
                    
                    {/* OTP Display */}
                    {ride.ride_otp && ride.status === 'accepted' && (
                      <div className="mt-3 p-3 bg-purple-100 rounded-lg">
                        <p className="text-sm text-purple-700 font-medium">
                          Ride OTP: <span className="text-lg font-bold">{ride.ride_otp}</span>
                        </p>
                        <p className="text-xs text-purple-600 mt-1">
                          Ask the rider to share this OTP to start the ride
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    {ride.status === 'accepted' && (
                      <>
                        <button
                          onClick={() => setSelectedRideForOTP(ride)}
                          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg transition-colors font-medium flex items-center justify-center"
                        >
                          <CheckCircle className="w-5 h-5 mr-2" />
                          Verify OTP & Start Ride
                        </button>
                        <button
                          onClick={() => handleCancelRide(ride)}
                          className="bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-lg transition-colors font-medium flex items-center"
                        >
                          <XCircle className="w-5 h-5 mr-2" />
                          Cancel
                        </button>
                      </>
                    )}
                    
                    {ride.status === 'in_progress' && (
                      <button
                        onClick={() => completeRide(ride.id)}
                        className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 px-4 rounded-lg transition-colors font-medium flex items-center justify-center"
                      >
                        <CheckCircle className="w-5 h-5 mr-2" />
                        Complete Ride
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Nearby Ride Requests (Hide when there are accepted rides) */}
          {acceptedRides.length === 0 && (
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Nearby Ride Requests</h2>
                <button
                  onClick={fetchRideRequests}
                  className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Refresh
                </button>
              </div>
              
              {rideRequests.length === 0 ? (
                <div className="text-center py-8">
                  <Car className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-500">No ride requests available</p>
                  <p className="text-sm text-gray-400 mt-2">Make sure you're online and in a good location</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {rideRequests.map((request) => (
                    <div 
                      key={request.id} 
                      className={`border rounded-lg p-4 transition-all ${
                        flashEffect ? 'bg-yellow-50 border-yellow-300 animate-pulse' : 'border-gray-200 hover:border-blue-300'
                      }`}
                    >
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <div className="flex items-center mb-2">
                            <MapPin className="w-4 h-4 text-green-600 mr-2" />
                            <span className="text-sm font-medium text-green-600">Pickup</span>
                          </div>
                          <p className="text-sm text-gray-800 mb-3">{request.pickup_address}</p>
                          
                          <div className="flex items-center mb-2">
                            <Navigation className="w-4 h-4 text-red-600 mr-2" />
                            <span className="text-sm font-medium text-red-600">Drop</span>
                          </div>
                          <p className="text-sm text-gray-800">{request.drop_address}</p>
                        </div>
                        
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            <div>
                              <span className="text-gray-600">Distance:</span>
                              <p className="font-medium">{request.estimated_distance} km</p>
                            </div>
                            <div>
                              <span className="text-gray-600">Fare:</span>
                              <p className="font-medium text-green-600">₹{request.estimated_fare}</p>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            <div>
                              <span className="text-gray-600">Rider:</span>
                              <p className="font-medium">{request.rider_name}</p>
                            </div>
                            <div>
                              <span className="text-gray-600">Vehicle:</span>
                              <div className="flex items-center">
                                <span className="mr-2">{getVehicleEmoji(request.preferred_vehicle_type)}</span>
                                <span className="font-medium capitalize">{request.preferred_vehicle_type}</span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex gap-2 pt-2">
                            <button
                              onClick={() => acceptRide(request.id)}
                              className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 px-3 rounded-lg transition-colors font-medium text-sm flex items-center justify-center"
                            >
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Accept Ride
                            </button>
                            <button
                              onClick={() => handleRejectRide(request)}
                              className="bg-red-600 hover:bg-red-700 text-white py-2 px-3 rounded-lg transition-colors font-medium text-sm flex items-center"
                            >
                              <XCircle className="w-4 h-4 mr-1" />
                              Reject
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Ride History */}
          {showHistory && (
            <div className="lg:col-span-3 bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Ride History</h2>
              
              {rideHistory.length === 0 ? (
                <div className="text-center py-8">
                  <Clock className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-500">No ride history available</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {rideHistory.map((ride) => (
                    <div key={ride.id} className="border rounded-lg p-4 border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <div className="flex items-center mb-2">
                            <MapPin className="w-4 h-4 text-green-600 mr-2" />
                            <span className="text-sm font-medium">Route</span>
                          </div>
                          <p className="text-sm text-gray-800">
                            {ride.pickup_address} → {ride.drop_address}
                          </p>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-gray-600">Status:</span>
                            <p className={`font-medium ${
                              ride.status === 'completed' ? 'text-green-600' :
                              ride.status === 'cancelled' ? 'text-red-600' :
                              'text-yellow-600'
                            }`}>
                              {ride.status}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-600">Fare:</span>
                            <p className="font-medium">₹{ride.estimated_fare}</p>
                          </div>
                        </div>
                        
                        <div className="text-sm">
                          <span className="text-gray-600">Date:</span>
                          <p className="font-medium">
                            {new Date(ride.created_at).toLocaleDateString()}
                          </p>
                          {ride.cancellation_reason && (
                            <div className="mt-2">
                              <span className="text-gray-600">Reason:</span>
                              <p className="text-red-600 text-xs">{ride.cancellation_reason}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* OTP Verification Modal */}
      {selectedRideForOTP && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Verify Ride OTP</h2>
                <button
                  onClick={() => setSelectedRideForOTP(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
              
              <div className="mb-6">
                <p className="text-sm text-gray-600 mb-4">
                  Ask the rider to provide the OTP to start the ride:
                </p>
                <div className="bg-gray-50 p-4 rounded-lg mb-4">
                  <p className="text-sm"><strong>From:</strong> {selectedRideForOTP.pickup_address}</p>
                  <p className="text-sm"><strong>To:</strong> {selectedRideForOTP.drop_address}</p>
                  <p className="text-sm"><strong>Rider:</strong> {selectedRideForOTP.rider_name}</p>
                </div>
                
                <input
                  type="text"
                  value={otpInput}
                  onChange={(e) => setOtpInput(e.target.value)}
                  placeholder="Enter 4-digit OTP"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-lg font-mono"
                  maxLength={4}
                />
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => setSelectedRideForOTP(null)}
                  className="flex-1 bg-gray-600 text-white py-3 px-4 rounded-lg hover:bg-gray-700 transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={verifyOtpAndStartRide}
                  disabled={!otpInput}
                  className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  Start Ride
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Ride Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Cancel Ride</h2>
                <button
                  onClick={() => setShowCancelModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
              
              <div className="mb-6">
                <p className="text-sm text-gray-600 mb-4">
                  Please select a reason for cancelling this ride:
                </p>
                
                <select
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select cancellation reason</option>
                  <option value="Vehicle breakdown - unable to continue">Vehicle breakdown - unable to continue</option>
                  <option value="Personal emergency">Personal emergency</option>
                  <option value="Traffic/road conditions">Traffic/road conditions</option>
                  <option value="Rider requested cancellation">Rider requested cancellation</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => setShowCancelModal(false)}
                  className="flex-1 bg-gray-600 text-white py-3 px-4 rounded-lg hover:bg-gray-700 transition-colors font-medium"
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
      )}

      {/* Reject Ride Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Reject Ride</h2>
                <button
                  onClick={() => setShowRejectModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
              
              <div className="mb-6">
                <p className="text-sm text-gray-600 mb-4">
                  Please select a reason for rejecting this ride:
                </p>
                
                <select
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select rejection reason</option>
                  <option value="Too far from pickup location">Too far from pickup location</option>
                  <option value="Going in different direction">Going in different direction</option>
                  <option value="Taking a break">Taking a break</option>
                  <option value="Vehicle issue">Vehicle issue</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => setShowRejectModal(false)}
                  className="flex-1 bg-gray-600 text-white py-3 px-4 rounded-lg hover:bg-gray-700 transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmRejectRide}
                  disabled={!rejectReason}
                  className="flex-1 bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  Reject Ride
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DriverDashboard;