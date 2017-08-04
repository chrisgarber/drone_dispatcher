__version__ = "0.1.1"

import requests
import numpy
import json
import time


earthRadius = 6371 #km
depoLat = -37.8168 #degrees
depoLon = 144.9622 #degrees
droneSpeed = 50 #km/h


# haversine formula
def haversine(theta):
	return numpy.sin(theta/2)**2


class location:
	def __init__(self, lat, lon):
		#locations are stored in degrees
		self.latitude = lat
		self.longitude = lon

	#returns a distance in km
	def getDistance(self, loc):
		lat1, lon1, lat2, lon2 = map(numpy.radians, [self.latitude, self.longitude, loc.latitude, loc.longitude])
		return 2*earthRadius*numpy.arcsin(numpy.sqrt(haversine(lat2-lat1) + (numpy.cos(lat1)*numpy.cos(lat2)*haversine(lon2-lon1))))

	@classmethod
	def from_dict(cls, d):
		return cls(d['latitude'], d['longitude'])

depoLocation = location(depoLat, depoLon)


class package:
	def __init__(self, destinationLoc, packageId, deadline):
		self.destination = destinationLoc
		self.packageId = packageId
		self.deadline = deadline
		
	@classmethod
	def from_dict(cls, d):
		return cls(location.from_dict(d['destination']), d['packageId'], d['deadline'])

	@classmethod
	def from_dict_list(cls, l):
		return [cls.from_dict(d) for d in l]
		


class drone:
	def __init__(self, time, droneId, location, packages, speed=droneSpeed, depo=depoLocation):
		self.lastKnownLocationTime = time
		self.lastKnownLocation = location
		self.droneId = droneId
		self.plannedDestinations = []
		self.timeWhenFree = time
		self.depo = depo
		self.speed = speed
		self.packages = []
		self.initPlan(packages)
		self.assigned = False

	@classmethod
	def from_dict(cls, dct, time):
		return cls(time, dct['droneId'], location.from_dict(dct['location']), package.from_dict_list(dct['packages']))

	def initPlan(self, packages):
		#if we hae a package we're going to deliver, assign it to the drone
		if len(packages) > 0:
			self.assignPackages(packages)
		#otherwise just go to depo
		else:
			self.addDestinations([self.depo])


	#adds the destinations to the planned list and adjusts the time it will be available accordingly
	def addDestinations(self, destinations):
		for destination in destinations:
			self.timeWhenFree += self.getTravelTime(destination,self.lastKnownLocation if len(self.plannedDestinations)==0 else self.plannedDestinations[-1])
			self.plannedDestinations.append(destination)

	#returns the time in seconds it will take this drone to get from one location to another
	def getTravelTime(self, loc1, loc2):
		return (loc1.getDistance(loc2)/self.speed)*3600

	#adds the package's destination to the planned list and adjusts the time it will be available accordingly
	def assignPackages(self, packages):
		for pack in packages:
			self.addDestinations([pack.destination, self.depo])
			self.assigned = True

	#returns the unix time a package would be delivered if assigned
	def getTimePackageWouldBeDelivered(self, pack):
		if self.timeWhenFree > time.time():
			self.timeWhenFree = time.time()
		return self.getTravelTime(pack.destination, self.lastKnownLocation if len(self.plannedDestinations)==0 else self.plannedDestinations[-1]) + self.timeWhenFree
				

class drone_dispatcher:
	def __init__(self):
		self.getDrones()
		self.getPackages()
		self.assignments = []
		self.unassignedPackages = []

	def getDrones(self):
		response = requests.get("https://codetest.kube.getswift.co/drones")
		responseTime = time.time()
		droneDict = response.json()
		# timeIter = [responseTime for i in droneDict]
		self.drones = [drone.from_dict(d, responseTime) for d in droneDict]
		if len(self.drones) != len(frozenset([d.droneId for d in self.drones])):
			raise ValueError("duplicate drone ids")
		self.unassignedDrones = len(self.drones)

	def getPackages(self):
		response = requests.get("https://codetest.kube.getswift.co/packages")
		self.packages = package.from_dict_list(response.json())
		if len(self.packages) != len(frozenset([pack.packageId for pack in self.packages])):
			raise ValueError("duplicate package ids")

	#this assigns the 
	def dispatchFastest(self, pack):
		#filter out all the drones assigned already
		unassignedDrones = [d for d in self.drones if not d.assigned]

		#if we have any drones left
		if len(unassignedDrones) != 0:
			#gets the drone that could deliver the package the soonest
			fastestDrone = min(unassignedDrones, key=lambda x: x.getTimePackageWouldBeDelivered(pack))

			#if that is soon enough add it to the list
			if fastestDrone.getTimePackageWouldBeDelivered(pack) < pack.deadline:
				self.assignments.append(assignment(fastestDrone.droneId, pack.packageId))
				# self.assignments.append({'packageId': pack.packageId, 'droneId': fastestDrone.droneId})
				fastestDrone.assignPackages([pack])
				return
		#otherwise add to the bad list
		self.unassignedPackages.append(pack)

	def dispatchDrones(self):
		for pack in self.packages:
			self.dispatchFastest(pack)
		
		#verify checksums, used mostly for debugging
		if len(self.packages) != (len(self.assignments) + len(self.unassignedPackages)):
			raise ValueError("packages must be in assignment list or unassigned list")
		assignedDrones = [a.droneId for a in self.assignments]
		if len(assignedDrones)!=len(frozenset(assignedDrones)):
			raise ValueError("Checksum failed. Drones assigned multiple times")
		assignedPackages = [a.packageId for a in self.assignments]
		if len(assignedPackages)!=len(frozenset(assignedPackages)):
			raise ValueError("Checksum failed. Package assigned multiple times")

		print("assignments: " + json.dumps(self.assignments, default=lambda o: o.__dict__))
		print("UnassignedPackageIds: " + json.dumps(self.unassignedPackages, default=lambda o: o.packageId))



class assignment(json.JSONEncoder):
	def __init__(self, droneId, packageId):
		self.droneId = droneId
		self.packageId = packageId
