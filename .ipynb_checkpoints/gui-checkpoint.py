##mcg_const = 1
##mcg = 2
from tkinter import *
from tkinter import filedialog
from tkinter import StringVar
from PIL import Image, ImageTk
import os
import matplotlib.pyplot as plt
import numpy as np
import glob
import pandas as pd
import cv2
import sys
from simpleicp import PointCloud, SimpleICP
        
class MainWindow():
    def __init__(self,main):
        self.main = main
        self.sift_judgement = ''
        self.main.title('Image Stitcher')
        self.main.geometry('1300x700')
        self.main.config(background = "white")
        self.stitch_mode = 'combo'
        ##Menu Bar
        menubar = Menu(main)
        self.main.config(menu=menubar)
        self.file_menu = Menu(menubar)
        self.file_menu.add_command(label = 'Save transform list', command = self.save_transform_list)
        self.file_menu.add_command(label = 'Load transform list',command=self.load_transform_list)
        self.file_menu.add_command(label = 'Bactch stitch images',command=self.batch_sititch_images)
        self.file_menu.add_command(label = 'Batch find drift correct transform', command=self.batch_find_drift_correct)
        self.file_menu.add_command(label = 'Batch drift correct', command = self.batch_drift_correct)
        self.file_menu.add_command(label = 'Alter SIFT and RANSAC params', command = self.sift_ransac_params)
        self.file_menu.add_command(label = 'Change Mode', command = self.change_mode)
        
        menubar.add_cascade(label = "File",menu=self.file_menu)
        self.last_filepath = '/'
        self.transform_dataframe = pd.DataFrame(columns = ['file1','file2','TM'])
        
        #Ransac and SIFT hyperparams
        self.ransac_recip_thresh= 0.99
        self.ransac_confidence = 0.99
        self.ransac_refine_iters = 10000
        self.numb_SIFT_points = 1000
        self.mode = 'stitching'
        
        
        ## Page
        self.transform = np.array([[1,0,0],[0,1,0]])
        
        tm_entry = StringVar()
        self.tm_entry_block = Entry(main,textvariable=tm_entry)
    
        self.button_load_tm = Button(main,
                                    text = "Perform TM from input",
                                    command = lambda: self.load_inputted_TM(tm_entry.get()))
        
        self.tm_from_selected_pts = Button(main,
                                    text = "Perform TM from\nselected points",
                                    command = self.tm_from_selection)
        
         
        self.button_explore = Button(main,
                                    text = "Browse Files",
                                    command = self.browseFiles)
        
        self.button_load_im1 = Button(main,
                                    text="Load First Image",
                                    command = lambda: self.loadimg(1))
        
        self.button_load_im2 = Button(main,
                                    text="Load Second Image",
                                    command = lambda: self.loadimg(2))
        
        self.button_sift = Button(main,
                                 text= "Detect keypoints and \nRANSAC estimation",
                                 command = self.siftestimation)
        
        self.button_icp = Button(main,
                                text = 'ICP refinement',
                                command = self.icp_refine)
        
        self.button_manual_points = Button(main,
                                    text = 'Select points manually',
                                    command = self.estimate_tm_manually)
        
        self.label_file_explorer = Label(main,
                            text = "Please select a file",
                            width = 50, height = 4,
                            fg = "blue")
        
        self.affine_label = Label(main,
                            text = str(self.transform),
                            width= 10, height=4,
                            fg = "black")
        
        self.button_save_transfom = Button(main, 
                                   text = 'Confirm Stitch and \nadd transform to list',
                                   command = self.add_transform_to_list)
        
        
        self.canvas1 = Canvas(main, height=500,width=500)
        self.canvas2 = Canvas(main, height=500,width=500)
        self.image_on_canvas1 = self.canvas1.create_image(0, 0, anchor='nw', image=None)
        self.image_on_canvas2 = self.canvas2.create_image(0, 0, anchor='nw', image=None)        
        self.label_file_explorer.grid(row = 0, column = 0,columnspan=2,sticky= N)
        self.button_explore.grid(row=1, column=0,columnspan = 2,sticky= N)
        self.button_load_im1.grid(row = 2, column = 0, sticky = N)
        self.button_load_im2.grid(row = 2, column = 1, sticky = N)
        self.button_manual_points.grid(row =3, column = 2, sticky = N)
        self.canvas1.grid(row=3, column=0,columnspan = 1, sticky = N)
        self.canvas2.grid(row=3, column=1,columnspan = 1, sticky = N)
        self.affine_label.grid(row=3, column=2, sticky=W)
        self.button_save_transfom.grid(row=3, column=3, columnspan=1, sticky=W)
        self.button_sift.grid(row=4, column=0, columnspan=1, sticky=N)
        self.button_icp.grid(row=4, column=1, columnspan=1, sticky=N)
        self.tm_entry_block.grid(row=2, column=2)
        self.button_load_tm.grid(row=2, column=3,sticky = N)
        self.tm_from_selected_pts.grid(row=3, column=3, sticky = N)
    


    def change_mode(self):
        '''Change between stitching and drift correction mode'''
        if self.mode == 'stitching':
            self.mode = 'drift correction'
        else:
            self.mode = 'stitching'
            
        print(f'Now in {self.mode} mode') 
        
        
    def tm_from_selection(self):
        self.transform,inliners = cv2.estimateAffinePartial2D(np.array(self.subplot1pts),np.array(self.subplot0pts),confidence= self.ransac_confidence,ransacReprojThreshold=self.ransac_recip_thresh,refineIters=self.ransac_refine_iters)
        
        # self.transform,inliners = cv2.estimateAffine2D(np.array(self.subplot1pts),np.array(self.subplot0pts),method = 'LMEDS',refineIters=self.ransac_refine_iters)
        
        
        
        
        
        
        
        
        
        self.affine_label.configure(self.affine_label, text=str(np.around(self.transform)))# Update affine label

        self.perform_transform()
         
            
    def estimate_tm_manually(self):
        
        def onclick(event):
    
            if event.dblclick:
                print(event.xdata,event.ydata)
                circle=plt.Circle((event.xdata,event.ydata),3,color='r')
                ax[event.inaxes.get_subplotspec().colspan[0]].add_patch(circle)
                fig.canvas.draw() #this line was missing earlier

                if event.inaxes.get_subplotspec().colspan[0] == 0:
                    self.subplot0pts.append([event.xdata,event.ydata])
                elif event.inaxes.get_subplotspec().colspan[0] == 1:
                    self.subplot1pts.append([event.xdata, event.ydata])


        self.subplot0pts = []
        self.subplot1pts = []


        fig,ax = plt.subplots(1,2)
        ax[0].imshow(self.npy1,cmap='gray')
        ax[1].imshow(self.npy2,cmap='gray')
        ax[0].set_xticks([])
        ax[0].set_yticks([])

        ax[1].set_xticks([])
        ax[1].set_yticks([])
        plt.suptitle('Select Correspondances with double click')

        fig.canvas.mpl_connect('button_press_event', onclick)
        plt.show()

        
    def browseFiles(self):
        self.filename = filedialog.askopenfilename(initialdir = self.last_filepath,
                                              title = "Select a File",
                                              filetypes = (("Image files",
                                                            "*.npy*"),
                                                           ("all files",
                                                            "*.*")))
        self.label_file_explorer.configure(text="File: "+ self.filename)
        self.last_filepath = self.filename
        

    def loadimg(self,canvas_num):
        if canvas_num == 1:
            self.npy1 = np.load(self.filename)
            npy = np.load(self.filename)
            npy = npy - np.amin(npy)
            npy = 255*(npy/np.amax(npy))
            self.imarray1 = npy.astype('uint8')
            img = ImageTk.PhotoImage(Image.fromarray(npy).resize((500, 500)))
            self.canvas1.image = img
            self.canvas1.itemconfig(self.image_on_canvas1, image=img)
            self.canvas1_filename = self.filename
            
        if canvas_num == 2:
            
            self.npy2 = np.load(self.filename)
            npy = np.load(self.filename)
            npy = npy - np.amin(npy)
            npy = 255*(npy/np.amax(npy))
            self.imarray2 = npy.astype('uint8')
            img = ImageTk.PhotoImage(Image.fromarray(npy).resize((500, 500)))
            self.canvas2.image = img
            self.canvas2.itemconfig(self.image_on_canvas2, image=img)
            self.canvas2_filename = self.filename
            
            
            
    def siftestimation(self):
        
        sift1 = cv2.SIFT_create()
        sift2 = cv2.SIFT_create()
        orb1 = cv2.ORB_create()   
        orb2 = cv2.ORB_create()
        brisk1 = cv2.BRISK_create()
        brisk2 = cv2.BRISK_create()
     

        
        self.features1b, self.descriptors1b = brisk1.detectAndCompute(self.imarray1,None)
        self.features2b, self.descriptors2b = brisk2.detectAndCompute(self.imarray2,None)    

        self.features1s, self.descriptors1s = sift1.detectAndCompute(self.imarray1, None)
        self.features2s, self.descriptors2s = sift2.detectAndCompute(self.imarray2, None)
        
      
        bf_b = cv2.BFMatcher(crossCheck = True)
        bf_s = cv2.BFMatcher(crossCheck = True)
        
        matches_b = bf_b.match(self.descriptors2b,self.descriptors1b)
        matches_s = bf_s.match(self.descriptors2s,self.descriptors1s)
       
        matches_b = sorted(matches_b, key = lambda x:x.distance)[:self.numb_SIFT_points] ## This nuber gives the number of matches to consider
        matches_s = sorted(matches_s, key = lambda x:x.distance)[:self.numb_SIFT_points] ## This nuber gives the number of matches to consider

        ## Get the points of xy1 and xy2 for the best 4 points ** NOTE- as images are the same mag but differet dimensions this makes things difficult
        src_points = []
        des_points = []
        
        
        
        if self.stitch_mode == 'sift':
            for match in matches_s:
                    feature1, feature2 = (self.features2s[match.queryIdx]), (self.features1s[match.trainIdx])
                    src_point  = int(feature1.pt[0]), int(feature1.pt[1])
                    des_point  = int(feature2.pt[0]),int(feature2.pt[1])
                    src_points.append(src_point)
                    des_points.append(des_point)
        
        elif self.stitch_mode == 'brisk':
            for match in matches_b:
                feature1, feature2 = (self.features2b[match.queryIdx]), (self.features1b[match.trainIdx])
                src_point  = int(feature1.pt[0]), int(feature1.pt[1])
                des_point  = int(feature2.pt[0]),int(feature2.pt[1])
                src_points.append(src_point)
                des_points.append(des_point)
        elif self.stitch_mode == 'combo':
            matches_list = [matches_b, matches_s]
            features_lits = [(self.features2b, self.features1b),(self.features2s,self.features1s)]
            for i in range(2):# Can get rid of this for loop if only using one of SIFT/orb/brisk
                matches = matches_list[i]
                self.features2, self.features1 = features_lits[i]
                for match in matches:
                    feature1, feature2 = (self.features2[match.queryIdx]), (self.features1[match.trainIdx])
                    src_point  = int(feature1.pt[0]), int(feature1.pt[1])
                    des_point  = int(feature2.pt[0]),int(feature2.pt[1])
                    src_points.append(src_point)
                    des_points.append(des_point)
            
            
        # img3 = cv2.drawMatches(self.imarray2,self.features2,self.imarray1,self.features1,matches,None,flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
        # if self.mode == 'stitching':
        #     fig,ax =plt.subplots()
        #     ax.imshow(img3)
        #     ax.set_xticks([])
        #     ax.set_yticks([])
        #     plt.show()
        
        
        try:
            self.transform,inliners = cv2.estimateAffinePartial2D(np.array(src_points), np.array(des_points),confidence= self.ransac_confidence,ransacReprojThreshold=self.ransac_recip_thresh,refineIters=self.ransac_refine_iters)
            self.affine_label.configure(self.affine_label, text=str(np.around(self.transform)))# Update affine label
            print(self.transform)
            
          
            #Add a santity check
            if self.mode == 'stitching':
                if (self.transform[0][0] < 0.95) & (self.transform[0][0] > 1.05):
                    print(self.transform, self.transform[0][0])
                    return
                self.perform_transform() #Call the transform function
                
                    

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(e)
            print(exc_type, exc_tb.tb_lineno)

    
            
    def sift_ransac_params(self):
        print('Current Pararmaters:')
        
        print(f'RANSAC Recip Threshold: {self.ransac_recip_thresh}\nRANSAC Confidence: {self.ransac_confidence}\nRANSAC Iterations: {self.ransac_refine_iters}\nNumber of SIFT keypoints: {self.numb_SIFT_points}')
        print('##############################')

        self.ransac_recip_thresh = float(input('Input a new RANAC recip thresh: '))
        self.ransac_confidence = float(input('Input a new RANSAC confidence: '))
        self.ransac_refine_iters = int(input('Input a new max number of RANSAC iterations: '))
        self.numb_SIFT_points = int(input('Input a new number of SIFT keypoitns: '))
        
        print('##############################')
        print('New Parameters:')
        print(f'RANSAC Recip Threshold: {self.ransac_recip_thresh}\nRANSAC Confidence: {self.ransac_confidence}\nRANSAC Iterations: {self.ransac_refine_iters}\nNumber of SIFT keypoints: {self.numb_SIFT_points}')

    
    


    
    
    def icp_refine(self):
        def array_to_xyz(im1):
            xyz = []
            im1_shape = np.shape(im1)
            for i in range(im1_shape[0]):
                for j in range(im1_shape[1]):
                    xyz.append([i,j,im1[i,j]])

            return np.array(xyz)
        
        print('icp_refine')
        overlap_index = np.where((self.t_canvas1>0) & (self.t_canvas2>0)) 
        canvas = self.t_canvas1[min(overlap_index[0]):max(overlap_index[0]),min(overlap_index[1]):max(overlap_index[1])]
        t_canvas = self.t_canvas2[min(overlap_index[0]):max(overlap_index[0]),min(overlap_index[1]):max(overlap_index[1])]
        xyz1 = array_to_xyz(canvas)
        xyz2 = array_to_xyz(t_canvas)
        # Create point cloud objects
        pc_fix = PointCloud(xyz1, columns=["x", "y", "z"])
        pc_mov = PointCloud(xyz2, columns=["x", "y", "z"])

        # Create simpleICP object, add point clouds, and run algorithm!
        icp = SimpleICP()
        icp.add_point_clouds(pc_fix, pc_mov)
        H, X_mov_transformed, rigid_body_transformation_params, distance_residuals = icp.run(correspondences=1000,max_overlap_distance=30,max_iterations=100,min_change =1)

            
        self.transform[0][-1] = self.transform[0][-1]-H[0][-1]#swapped with below
        self.transform[1][-1] = self.transform[1][-1]-H[1][-1]
        self.perform_transform()
        
        
        
        
    ## Functions from file dropdown    
    def add_transform_to_list(self):
       
        
        df2 = pd.DataFrame([[self.canvas1_filename,self.canvas2_filename,self.transform]],columns = ['file1','file2', 'TM'])
        self.transform_dataframe = pd.concat([self.transform_dataframe,df2])
            
        if self.mode == 'stitching':    
            os.remove(self.canvas1_filename)
    

        np.save(self.canvas2_filename,self.result)
        self.save_transform_list()#Save the updated df <----COMMENT BACK IN IF WANT CONTINUAL SAVING
        print('transform_added')
        
    def save_transform_list(self):
        print('Transform df head:')
        print(self.transform_dataframe.head())
        print('Transform df last item:')
        print(self.transform_dataframe.iloc[-1])
        self.transform_dataframe.to_pickle('transform_list')
        print('Transform list saved at:')
        print(os.getcwd())
        
    def load_transform_list(self):
        path = filedialog.askopenfilename(initialdir = self.last_filepath,
                                              title = "Select a File",
                                              filetypes = (("Pickle Files",
                                                            ""),
                                                           ("all files",
                                                            "*.*")))
        
        self.last_filepath = path
        
        self.transform_dataframe = pd.read_pickle(path)
        print('Loaded')
        print(self.transform_dataframe.head())
        
    def batch_sititch_images(self):
        self.batch_directory = filedialog.askdirectory(initialdir = self.last_filepath,
                                                      title = "Select a Directory")
        os.chdir(self.batch_directory)
        
        dirc_list = glob.glob('*.npy')
        print(dirc_list)
        self.sift_judgement = ''
        
        
        for file1 in dirc_list:
            
            print('STARTING NEW MATCHING IMAGE')
            self.filename = file1
            self.loadimg(1)
            for i,file2 in enumerate(dirc_list):
                print(i)
                self.filename = file2
                self.loadimg(2)
                
                self.siftestimation()
                
                if self.sift_judgement == 'break':
                    break
            if self.sift_judgement == 'break':
                break
                    
                
    def batch_drift_correct(self):
        self.mode = 'drift correction'
        self.batch_directory = filedialog.askdirectory(initialdir = self.last_filepath,
                                                      title = "Select a Directory")
        os.chdir(self.batch_directory)
        
        for i in range(len(self.transform_dataframe)):
            transform_to_be_applied = self.transform_dataframe['TM'].iloc[i]
            new_df = self.transform_dataframe.iloc[:i]
            print(transform_to_be_applied, new_df)
            for j in range(len(new_df)):
                self.filename = self.transform_dataframe['file1'].iloc[j]
                self.loadimg(1)
                self.filename = self.transform_dataframe['file2'].iloc[j]
                self.loadimg(2)
                self.perform_transform()
                self.add_transform_to_list()
                
    def batch_find_drift_correct(self):
        self.mode = 'drift correction'
      
        self.batch_directory = filedialog.askdirectory(initialdir = self.last_filepath,
                                                      title = "Select a Directory")
        os.chdir(self.batch_directory)
        dirc_list = glob.glob('*.npy')
        for i in range(len(dirc_list)-1):
            self.filename = str(i) + '.npy'
            self.loadimg(1)
            self.filename = str(i+1) + '.npy'
            self.loadimg(2)
            self.siftestimation()
        self.save_transform_list()
            

        
    def load_inputted_TM(self,inputted):
        inputted = list(map(int, inputted.split(',')))
        tm = np.array([[inputted[0],inputted[1],inputted[2]],
                        [inputted[3],inputted[-2],inputted[-1]]])
        self.transform = tm # Save new transform
        self.affine_label.configure(self.affine_label, text=str(tm))# Update affine label
        self.perform_transform() #Call the transform function
        
        
        
    def perform_transform(self):
        
        scale_factor = max(self.transform[0][0], self.transform[1][1])
        mcg_const_shape = np.shape(self.imarray1)
        mcg_shape = np.shape(self.imarray2)
        self.t_canvas1 = np.zeros((mcg_const_shape[0]+int((2*mcg_shape[0]*scale_factor))+500,mcg_const_shape[1]+int((2*mcg_shape[1]*scale_factor))+500)) # Want to be able to fit 2* image around your const img
        canvas2 = np.zeros((mcg_const_shape[0]+int((2*mcg_shape[0]*scale_factor))+500,mcg_const_shape[1]+int((2*mcg_shape[1]*scale_factor))+500))
        canvas_shape = np.shape(canvas2)
        print(canvas_shape)
        
        top_left_corn = (int((canvas_shape[0]-mcg_const_shape[0])/2),int((canvas_shape[1]-mcg_const_shape[1])/2))
        self.t_canvas1[top_left_corn[0]:top_left_corn[0] + int(mcg_const_shape[0]),top_left_corn[1]:top_left_corn[1] + int(mcg_const_shape[1])] = self.imarray1
        canvas2[top_left_corn[0]:top_left_corn[0] + int(mcg_shape[0]),top_left_corn[1]:top_left_corn[1] + int(mcg_shape[1]) ] = self.imarray2
        
        M = np.float32([[1, 0,-top_left_corn[1]+(top_left_corn[1]/self.transform[1][1])], #this correction of the mcg image was placed in the center- think if correct way round
                         [0, 1,-top_left_corn[0]+(top_left_corn[0]/self.transform[0][0])]])

        self.t_canvas2 = cv2.warpAffine(canvas2, M, (canvas_shape[1],canvas_shape[0]))
        
        
        self.t_canvas2 = cv2.warpAffine(self.t_canvas2, np.float32(self.transform), (canvas_shape[1],canvas_shape[0])) #Be careful here we may want to swap 0/1 
        
        
        ## Differentiate between modes
        if self.mode == 'stitching':
            self.result = cv2.addWeighted(self.t_canvas1, 1,self.t_canvas2, 1 , 0.0)
            self.plot_result()
            ## Get where result != canvas1 or canvas2 (the overlap) and make it = canvas1 (could equally use canvas2) so as not to get bright spot when during image blend
            not_equal_to_canv1 = self.result != self.t_canvas1
            not_equal_to_canv2 = self.result != self.t_canvas2
            self.result = np.where(np.logical_and(not_equal_to_canv1, not_equal_to_canv2),self.t_canvas1,self.result)
        
        elif self.mode == 'drift correction':
            self.result = self.t_canvas2
       
        ## Cut and plot
        self.result = self.result[~np.all(self.result == 0, axis=1)]
        self.result = self.result[:,~(self.result==0).all(0)]
        if self.mode == 'stitching':
            self.plot_result()
        

    def plot_result(self):
        ## Create a pop up with result
        
        fig,ax = plt.subplots()
        ax.imshow(self.result,cmap='gray')
        ax.set_xticks([])
        ax.set_yticks([])
        plt.show()
        
    
        
        
        
 
        
        

        

# Create the root window
root = Tk()
MainWindow(root)

# Let the window wait for any events
root.mainloop()