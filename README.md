# AttributesJoinByLine
AttributesJoinByLine allows you to copy attributes from the source layer to the target layer by using a line.


The plugin allows you to transfer attributes between two point layers. Points in both layers must be connected with lines. 
First, the algorithm searches for connected lines for the points of the source layer. If no touching lines were found at this stage, 
the algorithm will show an error message (along with the possibility of getting closer to the wrong object). Then, if you find a line, 
you search for objects from the source layer that are crossing on the line. Thanks to this, you can get a relationship of many points 
with data to one without data. If the target layer does not contain any field from the source layer, it will be automatically added. 
If more than one target has been found for one source point with completed data in the same column, it will be impossible to combine them 
,an error message will be displayed. The algorithm assumes that each of the three layers will be in the same coordinate system.

<img src="https://github.com/abocianowski/AttributesJoinByLine/blob/master/HowTo_gif/howto.gif?raw=true" alt="howto.gif">
