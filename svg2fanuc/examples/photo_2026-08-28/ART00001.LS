/PROG  ART00001
/ATTR
OWNER		= MNEDITOR;
COMMENT		= "svg2fanuc job 1";
PROG_SIZE	= 0;
CREATE		= DATE 26-09-08  TIME 12:00:00;
MODIFIED	= DATE 26-09-08  TIME 12:00:00;
FILE_NAME	= ;
VERSION		= 0;
LINE_COUNT	= 126;
MEMORY_SIZE	= 0;
PROTECT		= READ_WRITE;
TCD:  STACK_SIZE	= 0,
      TASK_PRIORITY	= 50,
      TIME_SLICE	= 0,
      BUSY_LAMP_OFF	= 0,
      ABORT_REQUEST	= 0,
      PAUSE_REQUEST	= 0;
DEFAULT_GROUP	= 1,*,*,*,*;
CONTROL_CODE	= 00000000 00000000;
/MN
   1:  UFRAME_NUM=1 ;
   2:  UTOOL_NUM=1 ;
   3:  CALL CELL_IN ;
   4:L P[1] 200mm/sec FINE ;
   5:L P[2] 30mm/sec FINE ;
   6:L P[3] 80mm/sec CNT3 ;
   7:L P[4] 80mm/sec CNT3 ;
   8:L P[5] 80mm/sec CNT3 ;
   9:L P[6] 80mm/sec CNT3 ;
  10:L P[7] 80mm/sec CNT3 ;
  11:L P[8] 80mm/sec CNT3 ;
  12:L P[9] 80mm/sec FINE ;
  13:L P[10] 30mm/sec FINE ;
  14:L P[11] 200mm/sec FINE ;
  15:L P[12] 30mm/sec FINE ;
  16:L P[13] 80mm/sec FINE ;
  17:L P[14] 30mm/sec FINE ;
  18:L P[15] 200mm/sec FINE ;
  19:L P[16] 30mm/sec FINE ;
  20:L P[17] 80mm/sec CNT3 ;
  21:L P[18] 80mm/sec CNT3 ;
  22:L P[19] 80mm/sec CNT3 ;
  23:L P[20] 80mm/sec CNT3 ;
  24:L P[21] 80mm/sec CNT3 ;
  25:L P[22] 80mm/sec CNT3 ;
  26:L P[23] 80mm/sec CNT3 ;
  27:L P[24] 80mm/sec CNT3 ;
  28:L P[25] 80mm/sec CNT3 ;
  29:L P[26] 80mm/sec CNT3 ;
  30:L P[27] 80mm/sec CNT3 ;
  31:L P[28] 80mm/sec CNT3 ;
  32:L P[29] 80mm/sec CNT3 ;
  33:L P[30] 80mm/sec CNT3 ;
  34:L P[31] 80mm/sec CNT3 ;
  35:L P[32] 80mm/sec CNT3 ;
  36:L P[33] 80mm/sec CNT3 ;
  37:L P[34] 80mm/sec CNT3 ;
  38:L P[35] 80mm/sec CNT3 ;
  39:L P[36] 80mm/sec FINE ;
  40:L P[37] 30mm/sec FINE ;
  41:L P[38] 200mm/sec FINE ;
  42:L P[39] 30mm/sec FINE ;
  43:L P[40] 80mm/sec FINE ;
  44:L P[41] 30mm/sec FINE ;
  45:L P[42] 200mm/sec FINE ;
  46:L P[43] 30mm/sec FINE ;
  47:L P[44] 80mm/sec FINE ;
  48:L P[45] 30mm/sec FINE ;
  49:L P[46] 200mm/sec FINE ;
  50:L P[47] 30mm/sec FINE ;
  51:L P[48] 80mm/sec FINE ;
  52:L P[49] 30mm/sec FINE ;
  53:L P[50] 200mm/sec FINE ;
  54:L P[51] 30mm/sec FINE ;
  55:L P[52] 80mm/sec CNT3 ;
  56:L P[53] 80mm/sec CNT3 ;
  57:L P[54] 80mm/sec CNT3 ;
  58:L P[55] 80mm/sec CNT3 ;
  59:L P[56] 80mm/sec CNT3 ;
  60:L P[57] 80mm/sec CNT3 ;
  61:L P[58] 80mm/sec FINE ;
  62:L P[59] 30mm/sec FINE ;
  63:L P[60] 200mm/sec FINE ;
  64:L P[61] 30mm/sec FINE ;
  65:L P[62] 80mm/sec FINE ;
  66:L P[63] 30mm/sec FINE ;
  67:L P[64] 200mm/sec FINE ;
  68:L P[65] 30mm/sec FINE ;
  69:L P[66] 80mm/sec CNT3 ;
  70:L P[67] 80mm/sec CNT3 ;
  71:L P[68] 80mm/sec FINE ;
  72:L P[69] 30mm/sec FINE ;
  73:L P[70] 200mm/sec FINE ;
  74:L P[71] 30mm/sec FINE ;
  75:L P[72] 80mm/sec FINE ;
  76:L P[73] 30mm/sec FINE ;
  77:L P[74] 200mm/sec FINE ;
  78:L P[75] 30mm/sec FINE ;
  79:L P[76] 80mm/sec CNT3 ;
  80:L P[77] 80mm/sec CNT3 ;
  81:L P[78] 80mm/sec CNT3 ;
  82:L P[79] 80mm/sec CNT3 ;
  83:L P[80] 80mm/sec CNT3 ;
  84:L P[81] 80mm/sec CNT3 ;
  85:L P[82] 80mm/sec CNT3 ;
  86:L P[83] 80mm/sec FINE ;
  87:L P[84] 30mm/sec FINE ;
  88:L P[85] 200mm/sec FINE ;
  89:L P[86] 30mm/sec FINE ;
  90:L P[87] 80mm/sec FINE ;
  91:L P[88] 30mm/sec FINE ;
  92:L P[89] 200mm/sec FINE ;
  93:L P[90] 30mm/sec FINE ;
  94:L P[91] 80mm/sec FINE ;
  95:L P[92] 30mm/sec FINE ;
  96:L P[93] 200mm/sec FINE ;
  97:L P[94] 30mm/sec FINE ;
  98:L P[95] 80mm/sec CNT3 ;
  99:L P[96] 80mm/sec CNT3 ;
 100:L P[97] 80mm/sec CNT3 ;
 101:L P[98] 80mm/sec CNT3 ;
 102:L P[99] 80mm/sec CNT3 ;
 103:L P[100] 80mm/sec CNT3 ;
 104:L P[101] 80mm/sec CNT3 ;
 105:L P[102] 80mm/sec CNT3 ;
 106:L P[103] 80mm/sec CNT3 ;
 107:L P[104] 80mm/sec CNT3 ;
 108:L P[105] 80mm/sec FINE ;
 109:L P[106] 80mm/sec CNT3 ;
 110:L P[107] 80mm/sec CNT3 ;
 111:L P[108] 80mm/sec CNT3 ;
 112:L P[109] 80mm/sec CNT3 ;
 113:L P[110] 80mm/sec FINE ;
 114:L P[111] 30mm/sec FINE ;
 115:L P[112] 200mm/sec FINE ;
 116:L P[113] 30mm/sec FINE ;
 117:L P[114] 80mm/sec CNT3 ;
 118:L P[115] 80mm/sec CNT3 ;
 119:L P[116] 80mm/sec CNT3 ;
 120:L P[117] 80mm/sec FINE ;
 121:L P[118] 30mm/sec FINE ;
 122:L P[119] 200mm/sec FINE ;
 123:L P[120] 30mm/sec FINE ;
 124:L P[121] 80mm/sec FINE ;
 125:L P[122] 30mm/sec FINE ;
 126:  CALL CELL_OUT ;
/POS
P[1]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 32.610  mm,	Y = 55.374  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[2]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 32.610  mm,	Y = 55.374  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[3]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 79.479  mm,	Y = 55.374  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[4]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 109.612  mm,	Y = 55.841  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[5]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 146.008  mm,	Y = 55.374  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[6]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 184.742  mm,	Y = 55.841  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[7]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 223.947  mm,	Y = 55.461  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[8]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 299.779  mm,	Y = 55.813  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[9]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 417.390  mm,	Y = 55.374  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[10]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 417.390  mm,	Y = 55.374  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[11]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 382.984  mm,	Y = 55.725  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[12]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 382.984  mm,	Y = 55.725  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[13]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 384.037  mm,	Y = 202.826  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[14]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 384.037  mm,	Y = 202.826  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[15]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 391.586  mm,	Y = 230.561  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[16]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 391.586  mm,	Y = 230.561  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[17]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 390.883  mm,	Y = 236.178  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[18]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 388.777  mm,	Y = 242.497  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[19]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 383.686  mm,	Y = 250.396  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[20]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 379.298  mm,	Y = 254.785  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[21]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 376.717  mm,	Y = 256.702  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[22]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 372.452  mm,	Y = 259.173  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[23]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 366.484  mm,	Y = 261.280  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[24]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 348.930  mm,	Y = 261.982  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[25]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 343.664  mm,	Y = 260.578  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[26]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 338.398  mm,	Y = 257.945  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[27]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 332.963  mm,	Y = 254.167  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[28]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 328.392  mm,	Y = 249.385  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[29]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 324.179  mm,	Y = 242.497  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[30]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 322.775  mm,	Y = 239.337  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[31]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 321.370  mm,	Y = 234.422  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[32]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 322.072  mm,	Y = 217.571  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[33]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 325.583  mm,	Y = 209.145  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[34]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 330.246  mm,	Y = 202.748  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[35]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 333.131  mm,	Y = 189.836  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[36]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 334.185  mm,	Y = 55.461  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[37]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 334.185  mm,	Y = 55.461  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[38]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 359.813  mm,	Y = 15.000  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[39]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 359.813  mm,	Y = 15.000  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[40]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 359.813  mm,	Y = 25.181  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[41]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 359.813  mm,	Y = 25.181  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[42]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 325.057  mm,	Y = 26.234  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[43]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 325.057  mm,	Y = 26.234  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[44]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 324.706  mm,	Y = 16.053  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[45]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 324.706  mm,	Y = 16.053  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[46]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 289.598  mm,	Y = 16.053  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[47]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 289.598  mm,	Y = 16.053  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[48]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 289.949  mm,	Y = 25.883  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[49]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 289.949  mm,	Y = 25.883  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[50]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 299.779  mm,	Y = 55.813  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[51]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 299.779  mm,	Y = 55.813  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[52]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 299.428  mm,	Y = 144.898  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[53]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 299.077  mm,	Y = 145.249  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[54]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 299.077  mm,	Y = 178.601  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[55]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 298.726  mm,	Y = 178.952  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[56]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 298.375  mm,	Y = 276.903  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[57]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 298.024  mm,	Y = 277.254  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[58]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 297.673  mm,	Y = 325.000  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[59]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 297.673  mm,	Y = 325.000  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[60]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 146.359  mm,	Y = 316.223  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[61]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 146.359  mm,	Y = 316.223  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[62]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 145.657  mm,	Y = 19.915  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[63]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 145.657  mm,	Y = 19.915  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[64]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 184.742  mm,	Y = 55.841  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[65]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 184.742  mm,	Y = 55.841  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[66]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 184.626  mm,	Y = 163.505  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[67]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 184.977  mm,	Y = 163.856  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[68]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 184.977  mm,	Y = 186.325  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[69]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 184.977  mm,	Y = 186.325  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[70]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.072  mm,	Y = 152.446  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[71]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.072  mm,	Y = 152.446  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[72]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 262.154  mm,	Y = 156.178  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[73]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 262.154  mm,	Y = 156.178  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[74]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.715  mm,	Y = 214.060  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[75]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.715  mm,	Y = 214.060  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[76]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.715  mm,	Y = 178.250  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[77]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.364  mm,	Y = 177.899  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[78]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.364  mm,	Y = 167.016  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[79]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.715  mm,	Y = 166.665  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[80]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.072  mm,	Y = 152.446  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[81]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.715  mm,	Y = 89.779  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[82]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.364  mm,	Y = 89.428  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[83]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.364  mm,	Y = 55.461  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[84]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 278.364  mm,	Y = 55.461  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[85]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 251.682  mm,	Y = 26.234  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[86]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 251.682  mm,	Y = 26.234  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[87]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 251.682  mm,	Y = 16.404  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[88]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 251.682  mm,	Y = 16.404  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[89]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 214.819  mm,	Y = 16.755  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[90]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 214.819  mm,	Y = 16.755  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[91]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 215.170  mm,	Y = 25.883  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[92]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 215.170  mm,	Y = 25.883  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[93]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 223.947  mm,	Y = 55.461  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[94]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 223.947  mm,	Y = 55.461  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[95]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 223.947  mm,	Y = 107.684  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[96]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 223.596  mm,	Y = 108.035  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[97]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 224.473  mm,	Y = 131.908  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[98]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 225.878  mm,	Y = 136.823  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[99]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 227.809  mm,	Y = 141.036  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[100]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 230.442  mm,	Y = 144.898  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[101]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 235.532  mm,	Y = 149.989  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[102]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 238.341  mm,	Y = 151.920  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[103]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 243.958  mm,	Y = 154.553  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[104]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 246.767  mm,	Y = 155.255  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[105]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 262.154  mm,	Y = 156.178  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[106]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 240.482  mm,	Y = 175.968  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[107]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 215.345  mm,	Y = 193.522  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[108]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 146.454  mm,	Y = 239.499  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[109]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 109.496  mm,	Y = 263.035  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[110]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 74.740  mm,	Y = 284.275  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[111]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 74.740  mm,	Y = 284.275  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[112]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 109.145  mm,	Y = 287.435  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[113]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 109.145  mm,	Y = 287.435  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[114]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 109.496  mm,	Y = 263.035  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[115]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 109.496  mm,	Y = 115.057  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[116]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 109.847  mm,	Y = 114.706  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[117]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 109.612  mm,	Y = 55.841  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[118]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 109.612  mm,	Y = 55.841  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[119]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 79.655  mm,	Y = 19.564  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[120]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 79.655  mm,	Y = 19.564  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[121]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 79.655  mm,	Y = 183.867  mm,	Z = 0.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
P[122]{
	GP1:
	UF : 1, UT : 1,		CONFIG : 'N U T, 0, 0, 0',
	X = 79.655  mm,	Y = 183.867  mm,	Z = 12.000  mm,
	W = 180.000 deg,	P = 0.000 deg,	R = 0.000 deg
};
/END
