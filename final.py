#Import libraries
import pygame
import random       
import sys
import math
from skimage.draw import line

class GridNode:
    def __init__(self, x, y, isWall):
        self.coords = {"x": x, "y": y}
        self.isWall = isWall
        
        self.occupant = []
        self.unknownMarker = False

    def addOccupant(self, occupant):
        self.occupant.append(occupant)

    def removeOccupant(self, occupant):
        self.occupant.remove(occupant) 

class Grid:
    def __init__(self, lenX, lenY, wallPercentage):
        self.size = {"x": lenX, "y": lenY }
        self.tileProperties = { "size" : 20, "margin" : 1 }
        self.wallPercentage = wallPercentage
        self.grid = []
        self.debugGrid = False

    def generate(self):
        for y in range(self.size["y"]):
            row = []
            for x in range (self.size["x"]):
                #For now, randomly assign IDs to the rows - either walls or empty tiles
                #If there's time later, gie option to place walls manually
                if(random.randint(1, 100) > self.wallPercentage):
                    row.append(GridNode(x, y, False))
                else:
                    row.append(GridNode(x, y, True))
            self.grid.append(row)
        
    def draw(self, screen):
        #Draw squares in rows and columns
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                #Draw tiles and margins according to properties
                tile = [
                    (self.tileProperties["margin"] + self.tileProperties["size"]) * x + self.tileProperties["margin"],
                    (self.tileProperties["margin"] + self.tileProperties["size"]) * y + self.tileProperties["margin"],
                    self.tileProperties["size"], self.tileProperties["size"]
                    ]
                #Pick colour based on tile contents
                if self.grid[y][x].isWall == False:
                    tileColour = WHITE
                else:
                    tileColour = BLACK

                if len (self.grid[y][x].occupant) > 0:
                    if isinstance(self.grid[y][x].occupant[0], Pickup):
                            tileColour = GREEN
                    elif isinstance(self.grid[y][x].occupant[0], Mouse):
                            tileColour = BLUE
                    elif isinstance(self.grid[y][x].occupant[0], Cat):
                            tileColour = RED
                
                #Draw the tile
                pygame.draw.rect(screen, tileColour, pygame.Rect(tile))

    def printText(self, hero):
        #Prints the map as ascii in the console
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if len(self.grid[y][x].occupant) > 0:
                    #Tile containing the current agent
                    if(self.grid[y][x].occupant[0] == hero):
                        print("A", end=" ")
                    #Tile containing another agent
                    else:
                        print("X", end=" ")
                #Tile containing a wall
                elif (self.grid[y][x].isWall):
                    print("■", end=" ")
                #Empty tile
                else:
                    print("□", end=" ")
            print("")
        print("\n")

class MemGrid(Grid):
    def __init__(self, lenX, lenY, wallPercentage):
        super().__init__(lenX, lenY, wallPercentage)

    def generate(self):
        #Generate a grid filled with unknown values to fill in later
        #Assumed not to have walls until seen
        for y in range(self.size["y"]):
            row = []
            for x in range (self.size["x"]):
                row.append(GridNode(x, y, False))
                row[x].unknownMarker = True
            self.grid.append(row)
            
    def printText(self, hero):
        #Prints the map as ascii in the console
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x].unknownMarker:
                    #Unknown Tile
                    print("?", end=" ")
                elif len(self.grid[y][x].occupant) > 0:
                    if(self.grid[y][x].occupant[0] == hero):
                        #Tile containing the current agent
                        print("A", end=" ")
                    else:
                        #Tile containing another agent
                        print("X", end=" ")
                elif (self.grid[y][x].isWall):
                    #Tile containing a wall
                    print("■", end=" ")
                else:
                    #Empty tile
                    print("□", end=" ")
            print("")
        print("\n")
    


class Option:
    def __init__(self, agent, x, y):
        self.target = {"x": x, "y": y}
        self.agent = agent
        self.label = "Generic Task"
        self.inProgress = False
        self.complete = False
        
class MoveToPos(Option):
    #Move towards a defined set of coordinates
    def __init__(self, agent, x, y, targetAgent):
        super().__init__(agent, x, y)
        self.plannedPath = []
        self.targetAgent = targetAgent
        self.label = ("Move Towards %s seen at [%i, %i]" % (self.targetAgent.niceName, x, y))

    def startTask(self):
        #Create a path towards a specified point
        self.plannedPath = self.agent.aStar([self.target["x"], self.target["y"]])
        if (self.plannedPath == None):
            self.complete = True
            return [0,0]
        self.inProgress = True
        return self.nextStep()
        
    def nextStep(self):
        #Follow preplanned path
        if len(self.plannedPath) > 0:
            nextMove = self.plannedPath[0]
            self.plannedPath.pop(0)
        else:
            self.complete = True
            return [0, 0]
        return nextMove


class Explore(Option):
    #Pick a random unknown tile and move towards it
    def __init__(self, agent):
        super().__init__(agent, 0, 0)
        self.plannedPath = []
        self.x = 0
        self.y = 0
        self.label = "Explore An Unknown Spot"
        self.fullyExplored = False

    def prepTask(self):
        #Refer to memory grid and retrieve an unknown space at random
        candidates = []

        #Iterate through all spaces and add all unknown tiles to candidate list
        for y in range(self.agent.memGrid.size["y"]):
            for x in range(self.agent.memGrid.size["x"]):
                if self.agent.memGrid.grid[y][x].unknownMarker:
                    candidates.append([x, y])

        #Pick random candidate. If no candidates exist, map is fully explored
        if len(candidates) > 0:
            chosenTile = random.choice(candidates)
            self.x = chosenTile[0]
            self.y = chosenTile[1]
        else:
            self.fullyExplored = True

        self.label = ("Explore the Unknown Spot at [%i, %i]" % (self.x, self.y))

    def startTask(self):
        #Plan a path to the randomised spot
        if(self.fullyExplored):
            #Shouldn't reach this point, but here as a fallback
            nextMove = [0,0]
        else:
            self.plannedPath = self.agent.aStar([self.x, self.y])
            if (self.plannedPath == None):
                self.complete = True
                return [0,0]
            self.inProgress = True
            return(self.nextStep())

    def nextStep(self):
        #Follow planned path

        #If trying to navigate to a wall tile, or agent is currently in target tile, abort task
        if(self.agent.memGrid.grid[self.y][self.x].isWall or [self.agent.position["x"], self.agent.position["y"]] == [self.x, self.y]):
            self.complete = True
            return [0,0]
        
        if len(self.plannedPath) > 0:
            nextMove = self.plannedPath[0]
            self.plannedPath.pop(0)
        else:
            self.complete = True
            return [0, 0]
        return nextMove

class Wander(Option):
    #Pick a random valid direction and move that way - last resort if there aren't any other options
    def __init__(self, agent):
        super().__init__(agent, 0, 0)
        self.label = ("Wander Randomly")

    def startTask(self):
        directions = self.agent.considerOptions(self.agent.position["x"], self.agent.position["y"], self.agent.memGrid)
        nextMove = random.choice(directions)
        self.inProgress = True
        return nextMove

    def nextStep(self):
        self.complete = True
        nextMove = self.startTask()
        return nextMove

class Hide(Option):
    #Pick the closest tile that an enemy agent can't see and move there
    def __init__(self, agent, threat):
        super().__init__(agent, 0, 0)
        self.plannedPath = []
        self.threat = threat
        self.label = ("Hide from %s at [%i, %i]" % (self.threat.niceName, self.threat.position["x"], self.threat.position["y"]))

    def startTask(self):
        targetTile = self.agent.runAway(self.threat)
        self.plannedPath = self.agent.aStar(targetTile)
        if (self.plannedPath == None):
                self.complete = True
                return [0,0]
        self.inProgress = True
        return self.nextStep()

    def nextStep(self):
        if len(self.plannedPath) > 0:
            nextMove = self.plannedPath[0]
            self.plannedPath.pop(0)
        else:
            return [0, 0]
        return nextMove
    
#Agents

class AgentBase:
    def __init__(self, energy, visionRange):
        self.energy = energy
        self.visionRange = visionRange
        
        self.entVisionCurrent = []
        self.entVisionMemory = []
        self.points = 0
        self.lifeTime = 0
        self.target = None
        self.memGrid = None
        self.agenda = []
        self.reevaluateNextMove = False
        self.killer = None

    def placeMe(self, grid, x, y):
        #Places the agent in a defined spot
        self.position = {"x": x, "y": y}
        grid.grid[y][x].addOccupant(self)

        self.genMemGrid(grid)

    def genMemGrid(self, grid):
        #Generate a new grid to represent the agent's memory of the environment
        self.memGrid = MemGrid(grid.size["x"], grid.size["y"], 0)
        self.memGrid.generate()

    def instantLearnGrid(self, grid):
        #Sets the memgrid to the grid, meaning the agent doesn't need to manually discover its surroundings
        self.memGrid = grid

    def getDistanceBetween(self, x1, y1, x2, y2):
        #Returns the distance between two sets of coords
        #Because diagonal movement isn't an option, this is simply the sum of the distances between X and Y coords
        return abs(x1 - x2) + abs(y1 - y2)

    def getDistanceFromMe(self, x, y):
        #Returns the distance between the agent and defined coords
        return(self.getDistanceBetween(self.position["x"], self.position["y"], x, y))
        
    def checkMove(self, grid, curX, curY, dirX, dirY):
        #Checks an adjacent tile and returns if it's a valid move or not
        targetX = curX + dirX
        targetY = curY + dirY
        
        #Check that target tile is within grid boundaries
        if(targetX > grid.size["x"] - 1 or targetY > grid.size["y"] - 1):
            return False
        elif (targetX < 0 or targetY < 0):
            return False

        #Check target tile for walls
        if (grid.grid[targetY][targetX].isWall):
            return False

        #Check target tile for instances of same agent
        #E.g. Prevent two mice from overlapping, but not a cat from catching a mouse
        for occupant in grid.grid[targetY][targetX].occupant:
            if type(occupant) is type(self):
                return False

        #Checks passed - target tile is a valid move
        return True

    def considerOptions(self, xPos, yPos, grid):
        #Go through all possible moves and eliminate invalid ones

        possibleMoves = [   #Could include diagonals (e.g. [1,1] is NE, but that would let the agent ignore diagonal walls
            [0, 1],     #N
            [1, 0],     #E
            [0, -1],    #S
            [-1, 0]     #W
            ]
        validMoves = []

        #Check each possible move to ensure it's valid
        for move in possibleMoves:
            if (self.checkMove(grid, xPos, yPos, move[0], move[1])):
                validMoves.append(move)
        
        #Return list of valid moves
        return validMoves

    def aStar(self, targetTile):
        #Adapted from https://www.youtube.com/watch?v=-L-WgKMFuhE&list=PLFt_AvWsXl0cq5Umv3pMC9SPnKjfp9eGW
        #Calculate path to a specified tile

        openList = []
        closedList = []

        counter = 0

        openList.append({
            "position": [self.position["x"], self.position["y"]],
            "gCost": 0,
            "hCost": self.getDistanceFromMe(targetTile[0], targetTile[1]),
            "parent": None
            })

        while len(openList) > 0:
            counter += 1

            #Break out of the loop if the pathfinding gets stuck - ideally shouldn't happen, but this is not an ideal world
            if (counter % 200 == 0):
                print(self.niceName + " stuck pathfinding - breaking out")
                return None
            
            #Find node in openList with lowest cost
            currentNode = openList[0]
            
            for node in openList:
                if ((node["gCost"] + node["hCost"]) < (currentNode["gCost"] + currentNode["hCost"])
                    or ((node["gCost"] + node["hCost"]) == (currentNode["gCost"] + currentNode["hCost"]) and (node["hCost"] < currentNode["hCost"]))):
                    currentNode = node

            #When found, remove from openList and add to closedList    
            openList.remove(currentNode)
            closedList.append(currentNode)
            
            #If currentNode is the target tile, path has been found
            if(currentNode["position"] == targetTile):
                #Retrace path
                path = []
                for item in closedList:
                    if(item["position"] == targetTile):
                        retraceNode = item
                        break

                while(retraceNode["parent"] is not None):
                    path.append(retraceNode["position"])
                    nextTile = retraceNode["parent"]
                    for item in closedList:
                        if(item["position"] == nextTile):
                            retraceNode = item
                            break
                #Reverse path - current to target instead of other way around
                path.reverse()

                #Convert to directions
                directions = []
                currentStep = [self.position["x"], self.position["y"]]
                for step in path:
                    directions.append([step[0] - currentStep[0], step[1] - currentStep[1]])
                    currentStep =  step
                    
                return directions

            #Check each neighbouring tile
            validMoves = self.considerOptions(currentNode["position"][0], currentNode["position"][1], self.memGrid)
            for move in validMoves:
                #Get position of each adjacent tile
                move[0] += currentNode["position"][0]
                move[1] += currentNode["position"][1]

                #If already in closedList, ignore
                for node in closedList:
                    if node["position"] == move:
                        continue
                    
                #Get distance costs
                moveGCost = currentNode["gCost"] + (abs(move[0] - currentNode["position"][0]) + abs(move[1] - currentNode["position"][1]))

                moveInfo = {
                    "position": move,
                    "gCost": moveGCost,
                    "hCost": abs(move[0] - targetTile[0]) + abs(move[1] - targetTile[1]),
                    "parent": currentNode["position"]
                    }
                
                newCost = currentNode["gCost"] + moveGCost

                inList = False
                oldGCost = 0
                for item in openList:
                    if (item["position"] == moveInfo["position"]):
                        inList = True
                        oldGCost = item["gCost"]

                if (moveGCost < oldGCost) or not inList:
                    openList.append(moveInfo)

    def directMove(self, targetTile):
        #If you can see a tile, there's already empty tiles between self and it - no need for astar
        validMoves = considerOptions(self.position["x"], self.position["y"], self.memGrid)

        smallestDist = 999
        bestMove = None

        for move in validMoves:
            #Calculate distance from target
            newPoint = [self.position["x"] + move[0], self.position["y"] + move[1]]
            dist = getDistanceBetween(targetTile[0], targetTile[1], newPoint[0], newPoint[1])
            #Get smallest distance
            if dist < smallestDist:
                smallestDist = dist
                bestMove = move

        return bestMove
            

    def whatsClosest(self):
        #Gather list of known objects
        knownObjs = self.entVisionCurrent
        pos = self.position

        #Find the object closest to the agent
        closestDist = 999
        closestObj = None

        for obj in knownObjs:
            #Ignore objects you don't want to target
            if not(isinstance(obj, self.targetType)):
                continue
            dist = (obj.position["x"] - pos["x"])**2 + (obj.position["y"] - pos["y"])**2
            if (closestDist > dist):
                closestDist = dist
                closestObj = obj

        #Set current target to nearest object
        self.target = closestObj

    def makeMove(self, grid, direction):
        #Remember old tile - set to empty once move is complete
        oldPos = [self.position["y"], self.position["x"]]

        #Move coords
        self.position["x"] += direction[0]
        self.position["y"] += direction[1]

        #It's going up to the grid size even though the target was one less so hopefully this sorts things
        if(self.position["x"] > (grid.size["x"] - 1)):
            self.position["x"] = (grid.size["x"] - 1)
        if(self.position["y"] > (grid.size["y"] - 1)):
            self.position["y"] = (grid.size["y"] - 1)
        
        #If target space has a pickup, run pickup code
        for occupant in grid.grid[self.position["y"]][self.position["x"]].occupant:
            if isinstance(occupant, self.targetType):
                self.pickup(grid)

        #Set tile on grid to new position
        grid.grid[oldPos[0]][oldPos[1]].removeOccupant(self)
        grid.grid[self.position["y"]][self.position["x"]].addOccupant(self)

    def runAway(self, danger):
        #Find closest point that's outside of the threat's vision and move to it
        dangerZone = danger.getVisibleTiles(self.memGrid)

        bestDist = 999
        bestSafePoint = None
        centre = [self.memGrid.size["x"] // 2, self.memGrid.size["y"] // 2]
        bestDistFromCentre = 999
        
        for y in range(self.memGrid.size["y"]):
            for x in range(self.memGrid.size["x"]):
                if not self.memGrid.grid[y][x].unknownMarker and not self.memGrid.grid[y][x].isWall and not ([x, y] == [self.position["x"], self.position["y"]]):
                    dist = self.getDistanceFromMe(x, y) - danger.getDistanceFromMe(x, y)
                    #Get best distance, weighed towards whatever's closest to the centre
                    if(dist < bestDist) or (dist == bestDist and bestDistFromCentre < self.getDistanceFromMe(centre[0], centre[1])):
                        bestDist = dist
                        bestSafePoint = [x, y]
                        bestDistFromCentre = self.getDistanceFromMe(centre[0], centre[1])

        return bestSafePoint

    def checkVision(self, grid):
        #Check what's in vision range

        #Get list of visible tiles
        visibleTiles = self.getVisibleTiles(grid)

        inVision = []
        newWalls = False

        #Check each visible tile for objects
        for tile in visibleTiles:
            #If tile in memory doesn't match current situation, update it
            if(self.memGrid.grid[tile[1]][tile[0]] != grid.grid[tile[1]][tile[0]]):
                self.memGrid.grid[tile[1]][tile[0]] = grid.grid[tile[1]][tile[0]]
                if (self.memGrid.grid[tile[1]][tile[0]].isWall):
                    newWalls = True
                
            #Current tile is occupied - examine its contents
            if len(grid.grid[tile[1]][tile[0]].occupant) > 0:
                for occupant in grid.grid[tile[1]][tile[0]].occupant:
                #If tile contains self, ignore it
                    if occupant == self:
                        continue
                    else:   
                        #If current object is already logged as in vision, ignore
                        if occupant in inVision:
                            continue
                        #Tile occupant isn't in the current vision list - add it
                        else:
                            for occupant in grid.grid[tile[1]][tile[0]].occupant:
                                if occupant not in self.entVisionMemory and occupant is not self:
                                    self.entVisionMemory.append(occupant)
                                inVision.append(occupant)

        #Compare list contents w/o caring about order
        if (set(self.entVisionCurrent) != set(inVision)):
            #If lists don't match, a new object has been found - reevaluate current agenda
            self.reevaluateNextMove = True

        #While moving, agent has discovered new walls
        #Next move should be reconsidered, so it doesn't try to follow an old path through them
        if(newWalls):
            self.reevaluateNextMove = True

        return inVision

    def getVisibleTiles(self, grid):
        #Find outer bounds of vision range
        inRange = (self.findMaxRange(grid))
        visibleTiles = []

        #Draw lines to find line of sight
        cenX = self.position["x"]; cenY = self.position["y"]
        
        for item in inRange:
            tarX = item[0]; tarY = item[1]
            lineX, lineY = line(cenX, cenY, tarX, tarY)


            #If line collides with wall, stop adding points to visible tile list
            for point in range(len(lineX)):
                #Remove edge case of points equaling the grid size, leading to out of range errors
                if(lineX[point] >= grid.size["x"]):
                    lineX[point] = grid.size["x"] - 1
                if(lineY[point] >= grid.size["y"]):
                    lineY[point] = grid.size["y"] - 1
                #Append to list if space isn't a wall
                if not grid.grid[lineY[point]][lineX[point]].isWall:
                    visibleTiles.append([lineX[point],lineY[point]])
                #If wall tile is encountered, stop following along the line
                else:
                    #Add wall tile to visible list, since you can see the walls themselves, just not through 'em
                    visibleTiles.append([lineX[point],[lineY[point]][0]])
                    #self.memGrid.grid[lineY[point]][lineX[point]].isWall = True
                    break

        #Remove duplicate tiles from list
        temp = visibleTiles
        visibleTiles = []

        for item in temp:
            if (item not in visibleTiles):
                visibleTiles.append(item)

        return visibleTiles

    def findMaxRange(self, grid):
        #Code adapted from https://www.redblobgames.com/grids/circle-drawing/
        centre = self.position
        radius = self.visionRange

        inRange = []

        #Find outer box around circle - don't check every tile in grid
        top = math.ceil(centre["y"] - radius)
        bottom = math.floor(centre["y"] + radius)

        #Find outer edges of circle
        for y in range(top, bottom + 1):
            dy = y - centre["y"]
            dx = math.sqrt(radius ** 2 - dy ** 2)
            left = math.ceil(centre["x"] - dx)
            right = math.floor(centre["x"] + dx)
            inRange.append([left, y])
            inRange.append([right, y])

        #Fill in gaps at top and bottom
        for r in range(math.floor(radius * math.sqrt(0.5))):
            d = math.floor((math.sqrt(radius ** 2 - r ** 2)))
            inRange.append([centre["x"] - d, centre["y"] + r])
            inRange.append([centre["x"] + d, centre["y"] + r])
            inRange.append([centre["x"] - d, centre["y"] - r])
            inRange.append([centre["x"] + d, centre["y"] - r])
            inRange.append([centre["x"] + r, centre["y"] - d])
            inRange.append([centre["x"] + r, centre["y"] + d])
            inRange.append([centre["x"] - r, centre["y"] - d])
            inRange.append([centre["x"] - r, centre["y"] + d])

        #Remove duplicates and out of range values
        prunedList = []
            
        for item in inRange:
            #If out of range, set to min/max value
            if(item[0] < 0):
                item[0] = 0
            elif(item[0] >= grid.size["x"]):
               item[0] = grid.size["x"] - 1
            elif(item[1] < 0):
               item[1] = 0
            elif(item[1] >= grid.size["y"]):
               item[1] = grid.size["y"] - 1
               
            if (item not in prunedList):
                prunedList.append(item)

        return prunedList

    def assessAgenda(self, grid):
        #Check surroundings
        self.entVisionCurrent = self.checkVision(grid)

        #Check neighbouring tiles - if target is present, go for that above all else
        skipEval = False
        validMoves = self.considerOptions(self.position["x"], self.position["y"], grid)
        for move in validMoves:
            for occupant in grid.grid[self.position["y"] + move[1]][self.position["x"] + move[0]].occupant:
                if(isinstance(occupant, self.targetType)):
                    nextMove = move
                    skipEval = True
                    

        if len(self.agenda) == 0:
            #If there's nothing in the agenda, well you should probably rethink your agenda, huh?
            self.reevaluateNextMove = True

        if self.reevaluateNextMove:
            #Stop following current agenda and make a new one
            self.agenda = []
            
            #Look for objects in vision
            distanceList = []
            threatList = []
            
            for obj in self.entVisionCurrent:
                #Look for targets and calculate how far away they are
                if self.fleeFrom is not None:
                    if isinstance(obj, self.fleeFrom):
                        threatList.append([obj, self.getDistanceFromMe(obj.position["x"], obj.position["y"])])
                    
                if isinstance(obj, self.targetType):
                    distanceList.append([obj, self.getDistanceFromMe(obj.position["x"], obj.position["y"])])

            #Look for objects in memory

            for obj in self.entVisionMemory:
                #Remember targets, do same as above
                if isinstance(obj, self.targetType):
                    #Don't add if already in list
                    objDist = [obj, self.getDistanceFromMe(obj.position["x"], obj.position["y"])]
                    if objDist not in distanceList:
                        distanceList.append(objDist)

            #Sort lists by distance, ascending
            threatList.sort(key=lambda threatList:threatList[1])
            distanceList.sort(key=lambda distanceList:distanceList[1])

            for target in distanceList:
                self.agenda.append(MoveToPos(self, target[0].position["x"], target[0].position["y"], target[0]))

            for threat in threatList:
                self.agenda.append(Hide(self, threat[0]))


            #Add Explore task to agenda
            self.agenda.append(Explore(self))
            self.agenda[-1].prepTask()
            if(self.agenda[-1].fullyExplored):
                self.agenda.pop(-1)

            #Add Wander task to agenda
            self.agenda.append(Wander(self))

        #Follow current agenda

        #Don't reevaluate next time unless something changes again
        self.reevaluateNextMove = False

        #Sort agenda based on agent's priority
        orderedAgenda = []
        priorityList = self.priorityList
        if (self.energy < 20):
            priorityList = self.direPriorityList
        for priority in priorityList:
            for task in self.agenda:
                if isinstance(task, priority):
                    orderedAgenda.append(task)

        self.agenda = orderedAgenda

        #Do current top-priority task
        if not skipEval:
            if not self.agenda[0].inProgress:
                nextMove = self.agenda[0].startTask()
            else:
                nextMove = self.agenda[0].nextStep()
                if self.agenda[0].complete:
                    self.agenda.pop(0)

        else:
            self.reevaluateNextMove = True

        if(nextMove == [0,0]):
            self.reevaluateNextMove = True
            self.agenda[0].complete = True
        
        self.makeMove(grid, nextMove)


    def reportStatsCurrent(self, grid):
        #Print out current stats
        print("\n\n\t\t", end="")
        print(self.niceName)
        print("\nCurrent Location: [%s, %s]" %(self.position["x"], self.position["y"]))
        print("Energy: %i" % self.energy)
        print("\nIn Vision:")
        if (len(self.entVisionCurrent) == 0):
            print("\tNo Objects")
        else:
            for item in self.entVisionCurrent:
                print("\t", end="")
                print(item.niceName)
                print("\t- Location: [%i, %i]" % (item.position["x"], item.position["y"]))

        print("\nIn Memory:")
        if (len(self.entVisionMemory) == 0 or set(self.entVisionMemory) == set(self.entVisionCurrent)):
            print("\tNo Objects Outside of Vision")
        else:
            for item in self.entVisionMemory:
                if item not in self.entVisionCurrent:
                    print("\t", end="")
                    print(item.niceName)
                    print("\t- Location: [%i, %i]" % (item.position["x"], item.position["y"]))


        print("______________________________")

        print("Agenda:")
        for task in self.agenda:
            print(" - ", end="")
            print(task.label)
        print("\n")

    def printMaps(self, grid):
        #Print maps as ascii, representing the agent's memory and their current vision
        print("Current Memory:")
        self.memGrid.printText(self)
        print("Current Vision:")
        self.printVision(grid)

    def printVision(self, grid):
        #Get the tiles the agent can currently see and print a map showcasing those
        visibleTiles = self.getVisibleTiles(grid)

        for y in range(len(self.memGrid.grid)):
            for x in range(len(self.memGrid.grid[0])):
                if [x,y] not in visibleTiles:
                    print("?", end=" ")
                elif len(self.memGrid.grid[y][x].occupant) > 0:
                    if self.memGrid.grid[y][x].occupant[0] == self:
                        print("A", end=" ")
                    else:
                        print("X", end=" ")
                elif (self.memGrid.grid[y][x].isWall):
                    print("■", end=" ")
                else:
                    print("□", end=" ")
            print("")
        print("\n")    

    def die(self, grid, killer):
        #Set the agent's killer depending on what killed it
        if(killer == None):
            self.killer = "Starvation"
        else:
            self.killer = killer

    def postMortem(self, grid):
        #Print out last stats before death
        print("\n\n\t\t", end="")
        print(self.niceName)
        print("\nLast Location: [%s, %s]" %(self.position["x"], self.position["y"]))
        print("Remaining Energy: %i" % self.energy)
        print("Lifetime: %i" % self.lifeTime)
        if not isinstance(self.killer, str):
            print("Killer: %s" % self.killer.niceName)
        else:
            print("Killer: %s" % self.killer)

        undiscovered = 0
        total = grid.size["x"] * grid.size["y"]
        for y in self.memGrid.grid:
            for x in y:
                if x.unknownMarker:
                    undiscovered += 1

        print("Percentage of Grid Explored: %i%%" % (((total - undiscovered) / total) * 100))

        print("\nPrevious Agenda:")
        for task in self.agenda:
            print(" - ", end="")
            print(task.label)
        print("\n")

        print("______________________________")

class Mouse(AgentBase):
    def __init__(self, energy, visionRange, energyFromPickup):
        super().__init__(energy, visionRange)
        self.energyFromPickup = energyFromPickup
        self.targetType = Pickup
        self.fleeFrom = Cat
        self.niceName = "Mouse"
        self.priorityList = [Hide, MoveToPos, Explore, Wander]
        self.direPriorityList = [MoveToPos, Hide, Explore, Wander]


    def pickup(self, grid):
        #Run pickup
        for item in grid.grid[self.position["y"]][self.position["x"]].occupant:
            if isinstance(item, Pickup):
                item.runPickup(grid, self)
                #Remove item from memgrid
                self.memGrid.grid[self.position["y"]][self.position["x"]].removeOccupant(item)
        

    def runPickup(self, grid, actor):
        #Mouse has been caught by a cat - remove from environment and give benefits to cat
        actor.entVisionCurrent.remove(self)
        actor.entVisionMemory.remove(self)

        actor.energy += self.energyFromPickup
        actor.points += 1

        self.die(grid, actor)


                    
        
        

class Cat(AgentBase):
    def __init__(self, energy, visionRange):
        super().__init__(energy, visionRange)
        self.targetType = Mouse
        self.fleeFrom = None
        self.niceName = "Cat"
        self.priorityList = [MoveToPos, Explore, Wander]
        self.direPriorityList = [MoveToPos, Explore, Wander]
        
    def pickup(self, grid):
        #Run pickup
        for item in grid.grid[self.position["y"]][self.position["x"]].occupant:
            if isinstance(item, self.targetType):
                item.runPickup(grid, self)
                self.memGrid.grid[self.position["y"]][self.position["x"]].removeOccupant(item)
    
    
class Pickup:
    def __init__(self, pickupEnergy):
        self.niceName = "Pickup"
        self.pickupEnergy = pickupEnergy

    def placeMe(self, grid):
        #Ensure target tile is within grid and isn't occupied
        empty = False
        while not (empty):
            x = y = -1
            #Make sure target tile is within grid bounds
            while((x < 0 or x > grid.size["x"] - 1) or (y < 0 or y > grid.size["y"] - 1)):
                x, y = self.pickRandomTile(grid)
            #If chosen tile is empty, exit loop
            if(len(grid.grid[y][x].occupant) == 0 and not grid.grid[y][x].isWall):
                empty = True

        #Set new position
        self.position = {"x": x, "y": y}
        grid.grid[y][x].addOccupant(self)

    def pickRandomTile(self, grid):
        #Picks a space in the grid entirely at random
        x = random.randint(0, grid.size["x"] -1)
        y = random.randint(0, grid.size["y"] -1)
        return x, y

    def runPickup(self, grid, actor):
        #The item has been picked up by another actor
        if(isinstance(actor, Mouse)):
            #Find the next spot to spawn in
            self.placeMe(grid)
            actor.entVisionCurrent.remove(self)
            actor.entVisionMemory.remove(self)

            #Pass values to actor
            actor.target = self.position
            actor.energy += self.pickupEnergy
            actor.points += 1
        else:
            #Respawn, but don't provide benefits, in case a cat happens to walk onto the tile
            self.placeMe(grid)
            actor.entVisionCurrent.remove(self)
            actor.entVisionMemory.remove(self)


#Colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GREY = (140, 140, 140)

def runGame(properties):
    #Generate a grid
    grid = Grid(properties["gridX"], properties["gridY"], properties["wallPercentage"])
    grid.generate()

    #Scale window based on grid size
    screenWidth = (grid.tileProperties["size"] * grid.size["x"]) + (grid.tileProperties["margin"] * (grid.size["x"] + 1))
    screenHeight = (grid.tileProperties["size"] * grid.size["y"]) + (grid.tileProperties["margin"] * (grid.size["y"] + 1))
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    clock = pygame.time.Clock()
    running = True

    #Init agents
    activeAgents = []
    environmentPickups = []
    graveyard = []

    #Add agents to the active agents list and give them names
    for i in range(properties["noCats"]):
        activeAgents.append(Cat(properties["catEnergy"], properties["catVis"]))
        if properties["noCats"] > 1:
            activeAgents[-1].niceName += " " + str(i + 1)

    for i in range(properties["noMice"]):
        activeAgents.append(Mouse(properties["mouseEnergy"], properties["mouseVis"], properties["energyFromMouse"]))
        if properties["noMice"] > 1:
            activeAgents[-1].niceName += " " + str(i + 1)

    for i in range(properties["noPickups"]):
        environmentPickups.append(Pickup(properties["energyFromPickup"]))
        environmentPickups[-1].placeMe(grid)

    #Place agents on the grid
    for agent in activeAgents:
        agent.placeMe(grid, random.randint(0, grid.size["x"] - 1), random.randint(0, grid.size["y"] - 1))        
        
    #Loop until program is quit
    while running:
        clock.tick(5) #FPS
        
        for event in pygame.event.get():
            #Quit button is clicked (i.e. red X on window)
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            #Listen for keypresses
            elif event.type == pygame.KEYDOWN:
                #When P key is pressed, pause
                if event.key == pygame.K_p:
                    pause(clock, grid)

        markedForDeath = []

        #Make decisions and move forward a turn (increase lifetime stat, decrease energy)
        for agent in activeAgents:
            #Make sure agent is still alive to act
            if agent.killer is None:
                agent.assessAgenda(grid)
                agent.energy -= 1
                agent.lifeTime += 1
            #If they ARE dead, mark them as such
            if(agent.energy <= 0 or agent.killer is not None):
                markedForDeath.append([agent, agent.killer])

        #Remove marked agents from environment
        for agent in markedForDeath:
            agent[0].die(grid, agent[1])
            activeAgents.remove(agent[0])
            graveyard.append(agent[0])

        #Draw grid
        screen.fill(GREY)
        grid.draw(screen)

        #Update display
        pygame.display.flip()
        pygame.display.update()

        #Check for end of game - all cats dead or all mice dead means time to stop
        mouseCount = 0
        catCount = 0
        for agent in activeAgents:
            if isinstance(agent, Mouse):
                mouseCount += 1
            elif isinstance(agent, Cat):
                catCount += 1
            
        if(mouseCount == 0 or catCount == 0):
            running = False

    #End of game report
    print("\n\nAlive:")
    for agent in activeAgents:
        agent.reportStatsCurrent(grid)
    print("\nDead:")
    for grave in graveyard:
        grave.postMortem(grid)

    

def pause(clock, grid):
    paused = True
    lastClick = [-1, -1]

    while(paused):
        for event in pygame.event.get():
        #Quit button is clicked (i.e. red X on window)
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                #P key pressed again - unpause
                if event.key == pygame.K_p:
                    paused = False
                    
            #Look for mouse clicks - any will work (LMB, RMB, MMB)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                #Find the ID of the tile being clicked
                gridX = event.pos[0] // (grid.tileProperties["size"] + grid.tileProperties["margin"])
                gridY = event.pos[1] // (grid.tileProperties["size"] + grid.tileProperties["margin"])
                print("Tile: [%i, %i]" % (gridX, gridY))

                #Print information about the tile
                tile = grid.grid[gridY][gridX]
                #Simple tiles - walls or empty spaces
                if len(tile.occupant) == 0:
                    if(tile.isWall):
                        print("Wall")
                    else:
                        print("Empty")
                #Tiles containing agents
                else:
                    #Pickups don't have much relevant information beyond their name
                    if(isinstance(tile.occupant[0], Pickup)):
                        print(tile.occupant[0].niceName)
                    #If agent isn't a pickup, it's a mouse or cat - report relevant stats
                    else:
                        #If clicked once, report regular stats
                        if lastClick != [gridX, gridY]:
                            tile.occupant[0].reportStatsCurrent(grid)
                        #If clicked more than once, print the agent's maps
                        else:
                            tile.occupant[0].printMaps(grid)
                            #Provide key for user's benefit
                            print("Key:")
                            print("? - Unknown")
                            print("□ - Empty")
                            print("■ - Wall")
                            print("A - Current Agent")
                            print("X - Other Entity")
                lastClick = [gridX, gridY]
        pygame.display.update()
        clock.tick(5)

def main():
    #Initialise pygame
    pygame.init()

    #Run the game - these values can be changed to alter the environment
    #(X Grid Size, Y Grid Size, Percentage of Wall Tiles, No. Cats, No. Mice, No. pickups)
    properties = {
        "gridX": 20,
        "gridY": 20,
        "wallPercentage": 10,
        "noCats": 1,
        "noMice": 3,
        "noPickups": 3,
        "catVis": 7.5,
        "mouseVis": 7.5,
        "catEnergy": 200,
        "mouseEnergy": 100,
        "energyFromPickup": 20,
        "energyFromMouse": 50
        }
    runGame(properties)
    input("")
        
main()
