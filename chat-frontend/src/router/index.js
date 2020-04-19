import Vue from 'vue'
import VueRouter from 'vue-router'
import Login from '../views/loginpage.vue'
import Homepage from '../views/homepage.vue'
import Gossippage from '../views/gossippage.vue'
import Logoutpage from '../views/logoutpage.vue'

import store from '../store'
import axios from  'axios'



Vue.use(VueRouter,store)

const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login
  },
  {
    path: '/about',
    name: 'About',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ '../views/About.vue')
  },
  {
    path : '/chat',
    component: Homepage,
    name : 'Homepage'
  },
  {
    path : '/rooms',
    component: Gossippage,
    name :'Chatrooms'
  },
  {
    path : '/logout',
    component : Logoutpage,
    name : 'Logout'
  
  }
 
]

const router = new VueRouter({
  routes,
  mode:'history'
})


router.beforeEach((to, from, next) =>
{
    
      console.log('in router : username = %s to.path = %s',store.state.user.username,to.path);
  
      if(to.path!== '/' && tokenExist() == false)
      {
      console.log('redirecting to /')
      next('/')
      }
      if(to.path!== '/logout' && tokenExist() && verifyToken() === false)
      {  console.log('redirecting to /logout')
        next('/logout')
      }

      next();
 })




function tokenExist(){
  if(typeof store.state.user == 'undefined' || store.state.user.username == null || store.state.user.key == null)
 {
  console.log('token does not exist') 
  return false
}
  return true
}


function verifyToken()
{
  
  var flag = false;

 
  console.log('here')
  const params = new URLSearchParams()
  params.append('username',store.state.user.username)
  params.append('token',store.state.user.key)
  axios.post(store.state.AUTHBASEURL+'token/verify/',params)
  .then(response=>{
      console.log('Verified token' + response.data)
      flag = response.data.verified;
  })
  .catch(error=>{
    console.log(error)
    flag = false;
  })  
  flag = true;

  return flag;

}


export default router
