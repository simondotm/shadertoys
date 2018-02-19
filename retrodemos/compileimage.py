import Image

# Script to convert bitmap images to encoded fragment shaders for use with ShaderToy
# Technique is to convert the bitmap data to a shader function that decodes the pixels from floats
# We cant use other techniques such as pre-initialized arrays, since WebGL only allows array lookups using consts

#----------------------- globals ---------------------------------
outputString = ""
tabCount = 0
# scroll to bottom of script to see the actions

#----------------------- functions ---------------------------------

# filename - the name of the image to process
# bitsPerPixel - specify how many bits are stored per pixel
# bitsPerFloat - specify how many bits are used in the packed floats (maximum 24)
def processImage(filename, bitsPerPixel, bitsPerFloat = 24.0):

	global outputString
	global tabCount
	# specify how many pixels to pack into one float
	pixelsPerFloat = bitsPerFloat / bitsPerPixel

	outputString = ""
	tabCount = 0

	def writeShader(l):
		global outputString
		# tabulate
		for i in range(tabCount):
			l = "\t" + l
			
		# add line	
		outputString += l
		outputString += "\n"
		#print "SHADER> " + l

	def tabShader(n):
		global tabCount
		tabCount += n
		if (tabCount < 0):
			tabCount = 0





	#----------------------- load image ---------------------------------


	im = Image.open(filename)




	print "image '" + filename + "' opened "

	width,height =  im.size

	print "image size w=" + str(width) + " h=" + str(height)


	pixels = im.load()

	print "image '" + filename + "' loaded "


		


	# determine width of image including padding (because image width may not exactly fit into the desired packing scheme)
	paddingSize = 4*int(pixelsPerFloat) # image width must be multiple of: 4 floats x number of pixels in each float
	paddedWidth = width
	if (width % paddingSize):
		paddedWidth += (paddingSize - width % paddingSize)
		
		
	print "Padded image width is " + str(paddedWidth) 
	
	# we can fit a variable number of pixels into one 24-bit float (using the integer part) depending on bits per pixel
	print "Pixels per float " + str(pixelsPerFloat)	
	print "Number of floats wide = " + str(paddedWidth / pixelsPerFloat) + "( " + str(paddedWidth / pixelsPerFloat / 4.0) + " vec4's)"


	# ----------------------------- process palette ---------------------------------------

	paletteSize = int(pow(2.0, bitsPerPixel))
	print "Palette contains " + str(paletteSize) + " colours"
	palette = im.palette
	#print palette

	# quantize RGB image to desired palette size - note this tends to sort colours by brightness and last colour is usually the bg color
	# you may need to modify the alpha in the output to get any transparency working
	im = im.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=paletteSize)	
	
	
	
	lut = im.resize((paletteSize, 1))
	lut.putdata(range(paletteSize))
	lut = list(lut.convert("RGB").getdata())
	lutsize = len(lut)	
	
	
	#print pixels

	data = list(im.getdata());

	#print data
	# debug test code
	if (False):
		print "Bitmap data:"
		for i in range(height):
			line = ""
			for j in range(width):
				idx = data[i*width + j]
				line += "%X" % idx
			print line	
	
	# ----------------------------- setup shader ---------------------------------------
	imageName = filename[:-4]
	writeShader("void drawSprite" + imageName + "( inout vec4 color, float x, float y )")
	writeShader("{")
	tabShader(1)


		

	# ----------------------------- encode bitmap ---------------------------------------

		

		

	def float2out(f):
		fmt = "{:0" + str(int(bitsPerFloat/4.0)) + "x}"
		return "0x" + fmt.format(int(f))



	def td2vec4(td):
		if (td[0] == td[1] == td[2] == td[3]):
			vec = "vec4(" + float2out(td[0]) + ")"
		else:
			vec = "vec4(" + float2out(td[0]) + ", " + float2out(td[1]) + ", " + float2out(td[2]) + ", " + float2out(td[3]) + ")" 
		return vec

	writeShader("")	
	writeShader("vec4 tile = vec4(0.0);")
	writeShader("")	


	writeShader("// unpack the bitmap on a row-by-row basis")

	for y in range(height):
		tile = ""
		tileDictionary = []
		vecDictionary = []
		pixelIndex = 0
		pixelValue = 0
		for x in range(paddedWidth):
			# apply padding by emitting zero entry pixels
			if (x >= width):
				idx = 0
			else:
				idx = data[y*width + x]
			# create tiles as reverse order nibbles
			tile = "%X" % idx + tile
			
			# add the new index
			pixelValue += idx * int(pow(2.0, pixelIndex*bitsPerPixel))
			pixelIndex += 1
			
			# once we have pixelsPerFloat pixels in the tile, we can flush the tile as a complete float
			#if ((x % pixelsPerFloat) == (pixelsPerFloat-1)):
			if (pixelIndex == pixelsPerFloat):
				# convert to base 16
				#n = int(tile, 16)
				#f = float(n)
				f = float(pixelValue)
				tileDictionary.append(f)
				#print "tile=" + tile + " f=" + str(f)
				tile = ""
				pixelValue = 0
				pixelIndex = 0
				
				# once we have 4 floats completed, we can flush out a vec4
				if (len(tileDictionary) == 4):
					vec = td2vec4(tileDictionary)
					vecDictionary.append(vec)
					tileDictionary = []
		



			
		outputRow = "if (y == " + str(float(y)) + ") tile = "
		pixelsPerVec = pixelsPerFloat * 4.0
		# flush the vec4's out
		columnOffset = pixelsPerVec
		for n in range(len(vecDictionary)):
			if (n == len(vecDictionary)-1):
				# last row
				outputRow += vecDictionary[n] + ";"
			else:
				outputRow += "( x < " + str(columnOffset) + " ) ? " + vecDictionary[n] + " : "
				
			columnOffset += pixelsPerVec
				
		writeShader(outputRow)
		#writeShader(( x < 16.0) ? " + vecDictionary[0] + " : ( x < 32.0 ) ? " + vecDictionary[1] + " : ( x < 48.0 ) ? " + vecDictionary[2] + " : " + vecDictionary[3] + ";")

	# ---------------- finish logic ---------------------------

	writeShader("")	
	writeShader("float n = mod(x, " + str(pixelsPerVec) + "); // quantize x coordinate to nearest " + str(int(pixelsPerVec)) + " pixels and get float containing " + str(int(pixelsPerFloat)) + " pixels")
	writeShader("float t = ( ( n < " + str(pixelsPerFloat) + " ) ? tile.x : ( n < " + str(pixelsPerFloat*2.0) + " ) ? tile.y : (n < " + str(pixelsPerFloat*3.0) + " ) ? tile.z : tile.w );")	
	writeShader("float p = mod( x, " + str(pixelsPerFloat) + " ) * " + str(bitsPerPixel) + "; // quantize x coordinate to nearest " + str(int(pixelsPerFloat)) + " pixels to determine pixel bit index")

	if (False):
		# old version - needs a divide
		writeShader("float s = floor( t / pow( 2.0, p ) ); // shift the float value down by the given bit index")
		writeShader("int idx = int(mod(s, " + str(pow(2.0, bitsPerPixel)) + ")); // mask off the lower bits to determine pixel index colour")
	else:
		# faster version has no division
		writeShader("int idx = int( mod( floor( t * exp2(-p) ), " + str(pow(2.0, bitsPerPixel)) + ")); // shift down by given bit index and mask off bits we need to determine pixel index colour");

	writeShader("")	



	# ----------------------------- output palette ---------------------------------------

	def rgb2float(c):
		f = c / 255.0
		fs = "%.6f" % f
		return fs

	def tuple2vec4(c, trans):
		v4 = "vec4(" + rgb2float(c[0]) + ", " + rgb2float(n[1]) + ", " + rgb2float(n[2])
		if (trans == True):
			v4 += ", 0.0)" 
		else:
			v4 += ", 1.0)"
		return v4
		
	# TODO: could maybe sort palette by most frequent colours to optimize on the assumption that shader will early out more frequently
	writeShader("// look up colour palette for the indexed pixel")
	idx = 0
	for n in lut:
		v4 = tuple2vec4(n, False) #idx == 0)
		writeShader("if (idx == " + str(idx) + ") color = " + v4 + ";")
		idx += 1
		


		
	tabShader(-1)
	writeShader("}")

	print "FINAL SHADER RESULTS\n"	
	print outputString

	f = open( imageName + ".txt", "w")
	f.write(outputString)
	f.close()

#----------------------- main ---------------------------------

#processImage("UnionDemoLogo.gif", 4.0, 24.0)
#processImage("UnionBackground.png", 2.0, 24.0)
#processImage("UnionLettersWhite.png", 1.0, 24.0)
#processImage("RedBall.png", 3.0, 24.0)
processImage("DemoFont.gif", 2.0, 24.0)

