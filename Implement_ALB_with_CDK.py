import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as elbv2 from '@aws-cdk/aws-elasticloadbalancingv2';

class WebEnvironmentStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Define the VPC
    const vpc = new ec2.Vpc(this, 'EngineeringVpc', {
      cidr: '10.0.0.0/18',
      maxAzs: 2
    });

    // Define the Internet Gateway and attach it to the VPC
    const igw = new ec2.CfnInternetGateway(this, 'EngineeringIGW');
    new ec2.CfnVPCGatewayAttachment(this, 'AttachGateway', {
      vpcId: vpc.vpcId,
      internetGatewayId: igw.ref,
    });

    // Define the Route Table
    const routeTable = new ec2.CfnRouteTable(this, 'EngineeringRouteTable', {
      vpcId: vpc.vpcId,
    });
    new ec2.CfnRoute(this, 'PublicRoute', {
      routeTableId: routeTable.ref,
      destinationCidrBlock: '0.0.0.0/0',
      gatewayId: igw.ref,
    });

    // Define the Security Group
    const sg = new ec2.SecurityGroup(this, 'WebserversSG', {
      vpc,
      description: 'Allow SSH and HTTP access',
    });
    sg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'Allow HTTP traffic');
    sg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), 'Allow SSH access');

    // Define EC2 instances
    const instanceType = new ec2.InstanceType('t2.micro');
    const machineImage = ec2.MachineImage.latestAmazonLinux();

    const instance1 = new ec2.Instance(this, 'WebServerInstance1', {
      vpc,
      instanceType,
      machineImage,
      securityGroup: sg,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,
      },
    });

    const instance2 = new ec2.Instance(this, 'WebServerInstance2', {
      vpc,
      instanceType,
      machineImage,
      securityGroup: sg,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,
      },
    });

    // Define the Load Balancer
    const lb = new elbv2.ApplicationLoadBalancer(this, 'EngineeringLB', {
      vpc,
      internetFacing: true,
    });

    const listener = lb.addListener('Listener', {
      port: 80,
    });

    const targetGroup = new elbv2.ApplicationTargetGroup(this, 'EngineeringWebservers', {
      vpc,
      port: 80,
      targets: [instance1, instance2],
    });

    listener.addTargetGroups('DefaultAction', targetGroup);

    // Outputs
    new cdk.CfnOutput(this, 'LoadBalancerURL', { value: lb.loadBalancerDnsName });
  }
}

const app = new cdk.App();
new WebEnvironmentStack(app, 'WebEnvironmentStack');
