import { useColorScheme } from 'react-native';
import { getTheme } from '../../theme';

export function useTheme() {
  return getTheme(useColorScheme());
}
