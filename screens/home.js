import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

export default function HomeScreen() {
  return (
    <SafeAreaView style={styles.container}>

      <LinearGradient
        colors={['#5B4CF0', '#4C8DF5']}
        style={styles.header}
      >
        <Text style={styles.headerText}>
          Bienvenido, aquí puedes ver y agregar tus maceats
        </Text>
      </LinearGradient>

      <View style={styles.content}>
        <TouchableOpacity style={styles.card}>
          <View style={styles.iconBox}>
            <Ionicons name="add" size={28} color="#fff" />
          </View>
          <Text style={styles.cardText}>Agregar maceta</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.bottomBar}>
        <TouchableOpacity style={styles.navBtn}>
          <Ionicons name="menu" size={26} color="#333" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.navBtn}>
          <Ionicons name="home" size={26} color="#333" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.navBtn}>
          <Ionicons name="person" size={26} color="#333" />
        </TouchableOpacity>
      </View>

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#EDEDED'
  },

  header: {
    paddingVertical: 30,
    paddingHorizontal: 20,
    alignItems: 'center'
  },

  headerText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center'
  },

  content: {
    padding: 20
  },

  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    borderRadius: 15,
    padding: 15,
    borderWidth: 2,
    borderColor: '#2D8CFF'
  },

  iconBox: {
    backgroundColor: '#5B4CF0',
    padding: 12,
    borderRadius: 10,
    marginRight: 15
  },

  cardText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000'
  },

  bottomBar: {
    position: 'absolute',
    bottom: 0,
    width: '100%',
    height: 70,
    backgroundColor: '#CFCFCF',
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center'
  },

  navBtn: {
    padding: 10,
    backgroundColor: '#BFBFBF',
    borderRadius: 10
  }
});