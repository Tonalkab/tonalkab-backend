import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  SafeAreaView,
  ScrollView,
  Modal,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

const COLORS = {
  primary: '#33A69C',
  accent: '#63C756',
  background: '#F0F4F3', 
  white: '#FFFFFF',
  text: '#2D3436',
  gray: '#A0A0A0',
};

const ASSETS = {
  logo: require('../assets/logo_tonalkab.png'), 
  flag: require('../assets/bandera.jpg'),
};

const InputField = ({ label, icon, placeholder, isPassword, isPhone, value, onChangeText }) => {
  const [hidden, setHidden] = useState(isPassword);

  return (
    <View style={styles.inputWrapper}>
      <Text style={styles.label}>{label}</Text>

      <View style={styles.inputBox}>
        {isPhone ? (
          <View style={styles.phoneGroup}>
            <Image source={ASSETS.flag} style={styles.flag} />
            <Text style={styles.code}>+52</Text>
          </View>
        ) : (
          <Ionicons name={icon} size={20} color={COLORS.primary} style={styles.icon} />
        )}

        <TextInput 
          style={styles.input} 
          placeholder={placeholder} 
          secureTextEntry={hidden}
          placeholderTextColor="#C0C0C0"
          value={value}
          onChangeText={onChangeText}
        />

        {isPassword && (
          <TouchableOpacity onPress={() => setHidden(!hidden)}>
            <Ionicons name={hidden ? 'eye-off' : 'eye'} size={20} color={COLORS.gray} />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

export default function LoginScreen({ navigation }) {

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [regNombre, setRegNombre] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regTelefono, setRegTelefono] = useState('');

  const [showRegister, setShowRegister] = useState(false);

  const handleLogin = async () => {
    try {
      const response = await fetch('http://192.168.1.110:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        navigation.navigate('Home');
      } else {
        alert(data.detail || 'Error al iniciar sesión');
      }

    } catch (error) {
      alert('Error de conexión');
    }
  };

  const handleRegister = async () => {
    try {
      const response = await fetch('http://192.168.1.110:8000/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nombre: regNombre,
          email: regEmail,
          password: regPassword,
          telefono: regTelefono,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        alert('Usuario registrado correctamente');
        setShowRegister(false);
        setRegNombre('');
        setRegEmail('');
        setRegPassword('');
        setRegTelefono('');
      } else {
        alert(data.detail || 'Error al registrar');
      }

    } catch (error) {
      alert('Error de conexión');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{flex: 1}}>
        <ScrollView contentContainerStyle={styles.scroll}>

          <View style={styles.brandSection}>
            <Image source={ASSETS.logo} style={styles.mainLogo} />
            <Text style={styles.appName}>TONALKAB</Text>
            <Text style={styles.tagline}>Sustentabilidad en tus manos</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.title}>¡Hola de nuevo!</Text>
            <Text style={styles.subtitle}>Ingresa tus credenciales para acceder.</Text>

            <InputField 
              label="Correo" 
              icon="mail-outline" 
              placeholder="correo@ejemplo.com"
              value={email}
              onChangeText={setEmail}
            />

            <InputField 
              label="Contraseña" 
              icon="lock-closed-outline" 
              placeholder="********" 
              isPassword
              value={password}
              onChangeText={setPassword}
            />

            <TouchableOpacity style={styles.forgot}>
              <Text style={styles.forgotText}>¿Olvidaste tu contraseña?</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.btnShadow} onPress={handleLogin}>
              <LinearGradient colors={[COLORS.primary, COLORS.accent]} style={styles.primaryBtn}>
                <Text style={styles.btnText}>ENTRAR</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity style={styles.footerLink} onPress={() => setShowRegister(true)}>
              <Text style={styles.footerText}>
                ¿No tienes cuenta? <Text style={styles.bold}>Regístrate</Text>
              </Text>
            </TouchableOpacity>
          </View>

        </ScrollView>
      </KeyboardAvoidingView>

      <Modal visible={showRegister} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>

            <View style={styles.handle} />

            <TouchableOpacity style={styles.closeIcon} onPress={() => setShowRegister(false)}>
              <Ionicons name="close-circle" size={30} color={COLORS.gray} />
            </TouchableOpacity>

            <Text style={styles.title}>Crear Cuenta</Text>

            <InputField 
              label="Nombre Completo" 
              icon="person-outline" 
              placeholder="Ej. Juan Pérez"
              value={regNombre}
              onChangeText={setRegNombre}
            />

            <InputField 
              label="Correo Electrónico" 
              icon="mail-outline" 
              placeholder="correo@ejemplo.com"
              value={regEmail}
              onChangeText={setRegEmail}
            />

            <InputField 
              label="Contraseña" 
              icon="lock-closed-outline" 
              placeholder="********" 
              isPassword
              value={regPassword}
              onChangeText={setRegPassword}
            />

            <InputField 
              label="Teléfono" 
              placeholder="(000) 000-0000" 
              isPhone
              value={regTelefono}
              onChangeText={setRegTelefono}
            />

            <TouchableOpacity onPress={handleRegister}>
              <LinearGradient colors={[COLORS.primary, COLORS.accent]} style={styles.primaryBtn}>
                <Text style={styles.btnText}>REGISTRARSE</Text>
              </LinearGradient>
            </TouchableOpacity>

          </View>
        </View>
      </Modal>

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scroll: { padding: 25, alignItems: 'center', flexGrow: 1 },

  brandSection: { alignItems: 'center', marginVertical: 30 },
  mainLogo: { width: 100, height: 100 },
  appName: { fontSize: 28, fontWeight: 'bold', color: COLORS.primary },
  tagline: { fontSize: 12, color: COLORS.accent },

  card: { backgroundColor: COLORS.white, borderRadius: 30, width: '100%', padding: 25 },
  title: { fontSize: 22, fontWeight: 'bold', textAlign: 'center' },
  subtitle: { textAlign: 'center', marginBottom: 20 },

  inputWrapper: { marginBottom: 15 },
  label: { fontWeight: 'bold' },
  inputBox: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#eee', borderRadius: 10 },
  icon: { marginRight: 10 },
  input: { flex: 1 },

  phoneGroup: { flexDirection: 'row', alignItems: 'center' },
  flag: { width: 20, height: 15 },
  code: { marginLeft: 5 },

  primaryBtn: { padding: 15, borderRadius: 10, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: 'bold' },

  modalOverlay: { flex: 1, justifyContent: 'flex-end' },
  modalSheet: { backgroundColor: '#fff', padding: 20, borderRadius: 20 },

  closeIcon: { position: 'absolute', right: 10, top: 10 },

  forgot: { alignSelf: 'flex-end', marginBottom: 10 },
  forgotText: { color: COLORS.primary },

  footerLink: { marginTop: 20, alignItems: 'center' },
  footerText: { color: COLORS.gray },
  bold: { color: COLORS.primary, fontWeight: 'bold' },
});