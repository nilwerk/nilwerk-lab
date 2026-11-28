// Runs before each test file, outside the per-test timeout. react-native exports its components lazily: without this, the first render in a
// file transforms and loads them inside the first test (about 3 s on a cold cache), which hit the 5 s test timeout on CI. Touching the exports the app uses moves that cost to setup.
const RN = require('react-native');
const USED = ['ActivityIndicator', 'Alert', 'Image', 'Linking', 'Modal', 'PermissionsAndroid', 'Platform', 'Pressable', 'RefreshControl', 'ScrollView', 'Share', 'StyleSheet', 'Text', 'TextInput', 'View', 'useColorScheme'];
for (const key of USED) void RN[key];
